"""Read-only content/catalog validation; never invent geography or translations."""
import json
from urllib.parse import urlsplit
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import Count
from core_apps.common.content_models import PublicContentPage, ReleaseNote
from core_apps.support.models import HelpContact, HelpArticle
from core_apps.properties.models import Governorate, City, District
from core_apps.features.student_models import University, Campus


def https_destination(value):
    try:
        p = urlsplit(value)
        return p.scheme == "https" and bool(p.hostname) and not p.username and not p.password and not p.fragment
    except ValueError:
        return False


def audit():
    models = (PublicContentPage, ReleaseNote, HelpContact, HelpArticle, Governorate, City, District, University, Campus)
    report = {"read_only": True, "network_fetch": False, "catalogs": {}, "missing": [], "invalid": [],
        "capabilities": {name: getattr(settings, name, None) for name in ("REVIEWS_ENABLED", "STUDENT_ENABLED_SERVICES", "COMPANY_HOUSING_ENABLED", "PLANNING_ENABLED_SERVICES")}}
    for model in models:
        rows = model.objects.order_by("pk")
        count = rows.count()
        report["catalogs"][model._meta.label] = {"count": count, "inspected": min(count, 50000), "truncated": count > 50000}
        if count == 0: report["missing"].append(model._meta.label)
        for row in rows[:50000].iterator():
            fields = []
            try:
                row.full_clean(validate_unique=False, validate_constraints=False)
            except ValidationError as error:
                fields.extend(error.message_dict.keys() if hasattr(error, "message_dict") else ["__all__"])
            for name in ("name", "name_ar", "name_en"):
                if hasattr(row, name) and not getattr(row, name).strip(): fields.append(name)
            if isinstance(row, (University, Campus)) and row.active:
                if not https_destination(row.source_url): fields.append("source_url")
                if not row.checked_on: fields.append("checked_on")
                if isinstance(row, Campus) and (row.latitude is None or row.longitude is None): fields.append("coordinates_unavailable")
            if isinstance(row, HelpContact) and row.active:
                if not row.phone and not row.email: fields.append("contact_destination")
                if not row.hours_ar or not row.hours_en: fields.append("localized_hours")
            if fields:
                report["invalid"].append({"model": model._meta.label, "id": str(row.pk), "fields": sorted(set(fields))})
    pages = set(PublicContentPage.objects.filter(active=True).values_list("slug", flat=True))
    report["missing_public_pages"] = sorted({"about-us", "privacy-policy", "terms"} - pages)
    report["missing_help_workspaces"] = sorted({"tenant", "owner"} - set(HelpContact.objects.filter(active=True).values_list("workspace", flat=True)))
    report["duplicate_university_names"] = University.objects.values("name_ar", "name_en").annotate(n=Count("pk")).filter(n__gt=1).count()
    report["approval_required"] = "Content, catalog provenance and unavailable coordinates require an authorized operator; this command changes nothing."
    return report


class Command(BaseCommand):
    help = "Audit managed content and catalog provenance without exposing text or changing data."
    def add_arguments(self, parser):
        parser.add_argument("--public-link", action="append", default=[], help="Explicit published URL as privacy=URL, terms=URL or contact=URL")
    def handle(self, **options):
        links = {}
        for value in options["public_link"]:
            key, sep, url = value.partition("=")
            if not sep or key not in {"privacy", "terms", "contact"} or key in links:
                raise CommandError("Use one explicit privacy/terms/contact URL each")
            links[key] = {"https_valid": https_destination(url), "availability": "not_fetched"}
        with transaction.atomic():
            if connection.vendor == "postgresql":
                with connection.cursor() as c:
                    c.execute("SET TRANSACTION READ ONLY")
                    c.execute("SET LOCAL statement_timeout = '15s'")
            result = audit()
        result["public_site_links"] = links
        result["uninspected_public_site_links"] = sorted({"privacy", "terms", "contact"} - set(links))
        self.stdout.write(json.dumps(result, sort_keys=True))
