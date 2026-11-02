"""Bounded consented signals and deterministic ordering of eligible results."""
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..renderers import FeatureJsonRenderer
from .access import require, scope_for, preferences
from .models import DiscoveryInteraction


class Priorities(serializers.Serializer):
    priorities = serializers.ListField(child=serializers.ChoiceField(choices=['price', 'space', 'amenities', 'commute']), max_length=3, allow_empty=True)
    budget_minor = serializers.IntegerField(min_value=1, max_value=10**12, required=False)
    price_period = serializers.ChoiceField(choices=['daily', 'weekly', 'monthly', 'yearly'], required=False)
    space = serializers.IntegerField(min_value=1, max_value=100000, required=False)
    amenities = serializers.ListField(child=serializers.CharField(max_length=50), max_length=30, required=False)
    commute_id = serializers.UUIDField(required=False)
    disabled_suggestions = serializers.ListField(child=serializers.ChoiceField(choices=['alternative', 'deadline']), required=False, default=list)
    behavioral_consent = serializers.BooleanField()
    suggestion_push = serializers.BooleanField(required=False, default=False)


def payload(item):
    from ..planning_models import CommuteSearch
    choices = [{'id': str(row.id), 'date': row.created_at.isoformat()} for row in CommuteSearch.objects.filter(
        user=item.user, status='succeeded', expires_at__gt=timezone.now()).order_by('-created_at')[:20]]
    return {**item.ranking, 'behavioral_consent': item.behavioral_consent,
            'suggestion_push': item.suggestion_push, 'algorithm_version': 1, 'commute_options': choices}


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def settings_view(request):
    require('discovery')
    scope = scope_for(request)
    with transaction.atomic():
        item = preferences(request.user, scope, lock=True)
        if request.method == 'DELETE':
            DiscoveryInteraction.objects.filter(preferences=item).delete()
            item.behavioral_consent = False
            item.save(update_fields=['behavioral_consent'])
        if request.method == 'POST':
            serializer = Priorities(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            ordered = data['priorities']
            if len(set(ordered)) != len(ordered):
                raise ValidationError('Priorities cannot be repeated.')
            if 'price' in ordered and not {'budget_minor', 'price_period'} <= data.keys():
                raise ValidationError('Enter a budget and its exact rental period.')
            if 'space' in ordered and 'space' not in data:
                raise ValidationError('Enter your preferred area.')
            if 'amenities' in ordered:
                from core_apps.properties.services.property import PropertyService
                if not data.get('amenities') or set(data['amenities']) - set(PropertyService.SUPPORTED_AMENITIES_MAP):
                    raise ValidationError('Choose current amenities.')
            if 'commute' in ordered:
                from ..planning_models import CommuteSearch
                if not data.get('commute_id') or not CommuteSearch.objects.filter(id=data['commute_id'], user=request.user,
                    status='succeeded', expires_at__gt=timezone.now()).exists():
                    raise ValidationError('Complete a current commute search first.')
                data['commute_id'] = str(data['commute_id'])
            item.behavioral_consent = data.pop('behavioral_consent')
            item.suggestion_push = data.pop('suggestion_push')
            item.ranking = data
            if not item.behavioral_consent:
                DiscoveryInteraction.objects.filter(preferences=item).delete()
            item.save(update_fields=['ranking', 'behavioral_consent', 'suggestion_push'])
        return Response(payload(item))


class Interaction(serializers.Serializer):
    property_id = serializers.UUIDField()
    offer_id = serializers.CharField(max_length=64, allow_blank=True, default='')
    kind = serializers.ChoiceField(choices=['open', 'favorite', 'compare'])
    active = serializers.BooleanField(default=True)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def interaction(request):
    require('discovery')
    scope = scope_for(request)
    serializer = Interaction(data=request.data); serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    with transaction.atomic():
        item = preferences(request.user, scope, lock=True)
        if not item.behavioral_consent:
            raise PermissionDenied('Interaction history is disabled.')
        from core_apps.properties.services.public_access import public_properties
        from core_apps.properties.models import Property
        from django.shortcuts import get_object_or_404
        prop = get_object_or_404(public_properties(Property.objects.all()), id=data['property_id'])
        if prop.rental_inventory and data['offer_id'] not in {str(o['id']) for o in prop.rental_inventory.get('offers', []) if not o.get('archived')}:
            raise ValidationError('Choose the exact current accommodation offer.')
        query = DiscoveryInteraction.objects.filter(preferences=item, property=prop, offer_id=data['offer_id'], kind=data['kind'])
        if not data['active']:
            query.delete()
        else:
            query.get_or_create(preferences=item, property=prop, offer_id=data['offer_id'], kind=data['kind'], day=timezone.localdate())
        DiscoveryInteraction.objects.filter(day__lt=timezone.localdate() - timedelta(days=29)).delete()
    return Response({'recorded': True})


def number(value):
    try:
        result = Decimal(str(value))
        return float(result) if result.is_finite() and result >= 0 else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def rank(queryset, request):
    require('discovery')
    if not request.user.is_authenticated:
        raise PermissionDenied('Sign in to use personal priorities.')
    scope = scope_for(request)
    item = preferences(request.user, scope)
    criteria = item.ranking.get('priorities', [])
    if not criteria:
        raise ValidationError('Choose your housing priorities first.')
    if queryset.count() > 500:
        raise ValidationError('Narrow the area or filters before personalizing these results.')
    signals = {}
    if item.behavioral_consent:
        for signal in DiscoveryInteraction.objects.filter(preferences=item, day__gte=timezone.localdate() - timedelta(days=29)):
            key = (signal.property_id, signal.offer_id)
            signals[key] = min(10, signals.get(key, 0) + {'open': 1, 'compare': 2, 'favorite': 3}[signal.kind])
    commute = {}
    if 'commute' in criteria:
        from ..planning_models import CommuteSearch
        record = CommuteSearch.objects.filter(id=item.ranking.get('commute_id'), user=request.user, status='succeeded', expires_at__gt=timezone.now()).first()
        if record:
            commute = {str(row.get('property_id')): row for row in record.matches}
    matches = getattr(request, 'student_offer_matches', {})
    ranked = []
    for prop in queryset:
        eligible = matches.get(prop.pk)
        scores, unknown = {}, []
        price = number(getattr(prop, 'student_comparison_price', None))
        period = request.query_params.get('price_period')
        if not prop.rental_inventory:
            price, period = number(prop.price), prop.price_period
        elif eligible is None:
            # A physical unit cannot inherit the parent price or mixed periods.
            price = None
        for criterion in criteria:
            value = None
            if criterion == 'price' and price is not None and period == item.ranking.get('price_period'):
                budget = item.ranking['budget_minor'] / 100
                value = max(0, min(1, 1 - price / (budget * 2)))
            elif criterion == 'space':
                area = number(prop.space)
                if area is not None and not prop.rental_inventory:
                    value = min(1, area / item.ranking['space'])
            elif criterion == 'amenities':
                # Shared property facts, not invented private-room amenities.
                from core_apps.properties.services.property import PropertyService
                wanted = item.ranking['amenities']
                fields = [PropertyService.SUPPORTED_AMENITIES_MAP[k] for k in wanted]
                value = sum(bool(getattr(prop, f, False)) for f in fields) / len(fields)
            elif criterion == 'commute':
                travel = commute.get(str(prop.id), {})
                journeys = travel.get('estimates', [])
                seconds = [number(j.get('duration_seconds')) for j in journeys]
                minutes = max(seconds) / 60 if seconds and all(s is not None for s in seconds) else None
                if minutes is not None:
                    value = 1 / (1 + minutes / 30)
            if value is None:
                unknown.append(criterion)
            scores[criterion] = value or 0
        weights = list(range(3, 3 - len(criteria), -1))
        explicit = sum(scores[c] * w for c, w in zip(criteria, weights)) / sum(weights)
        behavior = max((v for (pid, oid), v in signals.items() if pid == prop.pk and (eligible is None or oid in {str(v) for v in eligible})), default=0) / 10
        total = explicit if not signals else explicit * .8 + behavior * .2
        prop._experience_ranking = {'version': 1, 'priorities': criteria, 'unknown': unknown,
            'behavior_used': bool(signals), 'tradeoffs': [c for c in criteria if c not in unknown and scores[c] < .5]}
        ranked.append((total, str(prop.id), prop))
    return [p for _, _, p in sorted(ranked, key=lambda row: (-row[0], row[1]))]
