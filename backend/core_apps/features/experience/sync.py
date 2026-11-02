"""Private, allowlisted, three-way preference sync. No business commands."""
import copy
import base64
import binascii
import hashlib
import json
import uuid
from rest_framework.exceptions import ValidationError
from ..services.rental_phase2 import RentalConflict
from .models import ExperienceVersion, ExperienceOperation

NAMESPACES = {
    'discovery_folders', 'discovery_pins', 'home_shortcuts', 'quick_reply_pins',
    'company_pins', 'tenant_visit_filters', 'owner_visit_filters',
    'owner_property_filters', 'owner_listing_templates', 'student_plan_templates',
    'family_scope_templates', 'owner_weekly_availability', 'company_request_templates',
}


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def validate(content):
    if not isinstance(content, dict) or len(content) > 1000 or len(json.dumps(content).encode()) > 250_000:
        raise ValidationError('Invalid preference document size.')
    for key, value in content.items():
        namespace = key.split(':', 1)[0]
        if namespace not in NAMESPACES or len(key) > 512:
            raise ValidationError('Unsupported preference namespace.')
        if not isinstance(value, (dict, list, str)) or len(json.dumps(value).encode()) > 50_000:
            raise ValidationError('Invalid preference value.')
        if namespace == 'discovery_pins' and (not isinstance(value, list) or len(value) > 3):
            raise ValidationError('At most three saved property pins are supported.')
        if namespace == 'company_pins' and (not isinstance(value, list) or len(value) > 5):
            raise ValidationError('At most five company pins are supported.')
        # Explicit projection, never the recently-viewed or media snapshots store.
        if namespace in {'discovery_pins', 'discovery_folders'}:
            if namespace == 'discovery_folders' and not isinstance(value, dict):
                raise ValidationError('Invalid folder.')
            bookmarks = value if namespace == 'discovery_pins' else value.get('items', [])
            if namespace == 'discovery_folders' and set(value) - {'id', 'name', 'items'}:
                raise ValidationError('Unknown folder fields.')
            if not isinstance(bookmarks, list) or len(bookmarks) > 100:
                raise ValidationError('Invalid folder items.')
            for item in bookmarks:
                if not isinstance(item, dict) or set(item) - {'property_id', 'offer_id', 'title', 'at'}:
                    raise ValidationError('Unknown bookmark fields.')
    return content


def validate_scope(content, scope):
    if not scope.startswith('company/'):
        if any(key.split(':', 1)[0] in {'company_pins', 'company_request_templates'} for key in content):
            raise ValidationError('Company pins require a current company role.')
        return
    _, company, role = scope.split('/')
    for key in content:
        parts = key.split(':')
        if len(parts) != 3 or parts[0] not in {'company_pins', 'company_request_templates', 'home_shortcuts'}:
            raise ValidationError('Only choices for this company role can be synchronized.')
        try:
            record_scope = base64.b64decode(parts[1], altchars=b'-_', validate=True).decode('utf-8')
        except (ValueError, binascii.Error):
            raise ValidationError('Invalid company preference scope.') from None
        expected = f'company/{company}:{role}' if parts[0] == 'home_shortcuts' else f'{company}/{company}:{role}'
        if record_scope != expected:
            raise ValidationError('The preference belongs to another company role.')


def payload(item):
    return {'scope': item.scope, 'revision': item.revision, 'content': item.content,
            'conflicts': item.conflicts, 'tombstones': item.tombstones}


def merge(item, data):
    try:
        operation = uuid.UUID(str(data['operation_id']))
        revision = int(data['base_revision'])
    except (ValueError, TypeError, KeyError):
        raise ValidationError('A stable operation ID and base revision are required.')
    digest = fingerprint(data)
    receipt = ExperienceOperation.objects.filter(preferences=item, operation_id=operation).first()
    if receipt:
        if receipt.fingerprint != digest:
            raise RentalConflict('This operation ID was already used for different preferences.')
        return
    if revision < 0 or revision > item.revision:
        raise ValidationError('Invalid preference revision.')
    incoming = validate(data.get('content'))
    validate_scope(incoming, item.scope)
    if revision == item.revision:
        base = item.content
    elif revision == 0:
        base = {}
    else:
        version = ExperienceVersion.objects.filter(preferences=item, revision=revision).first()
        if not version:
            raise RentalConflict('Reload preferences before merging this device.')
        base = version.content
    merged = copy.deepcopy(item.content)
    for key in sorted(set(base) | set(incoming)):
        old, new, current = base.get(key), incoming.get(key), item.content.get(key)
        if old == new:
            continue
        if new is None:
            merged.pop(key, None)
            item.tombstones[key] = item.revision + 1
            if current not in (old, None):
                item.conflicts[key] = {'base': old, 'current': None, 'incoming': current, 'revision': item.revision + 1}
        elif item.tombstones.get(key, 0) > revision or (current != old and current != new):
            item.conflicts[key] = {'base': old, 'current': current, 'incoming': new, 'revision': item.revision + 1}
        else:
            merged[key] = new
    resolutions = data.get('resolutions', {})
    if not isinstance(resolutions, dict):
        raise ValidationError('Invalid conflict resolutions.')
    for key, choice in resolutions.items():
        conflict = item.conflicts.get(key)
        if not conflict or revision != item.revision or choice not in {'current', 'incoming'}:
            raise RentalConflict('Refresh the conflict before resolving it.')
        value = conflict[choice]
        if value is None:
            merged.pop(key, None)
            item.tombstones[key] = item.revision + 1
        else:
            merged[key] = value
            item.tombstones.pop(key, None)
        del item.conflicts[key]
    validate(merged)
    validate_scope(merged, item.scope)
    item.content = merged
    item.revision += 1
    item.save(update_fields=['content', 'revision', 'tombstones', 'conflicts'])
    ExperienceVersion.objects.create(preferences=item, revision=item.revision, content=item.content)
    ExperienceOperation.objects.create(preferences=item, operation_id=operation, fingerprint=digest)
