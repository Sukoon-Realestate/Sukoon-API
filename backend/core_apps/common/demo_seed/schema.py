"""Deterministic baseline records for model/admin coverage, not real transactions.

Bulk inserts deliberately avoid signals, provider calls and workflow services.
Database foreign keys, unique constraints and check constraints remain enforced.
Curated app-facing scenarios are built separately in scenarios.py.
"""
import hashlib
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

NAMESPACE = uuid.UUID("c1bef247-63d7-4af0-bde1-2ec3d6b3fc37")


def identity(value):
    return uuid.uuid5(NAMESPACE, value)


def application_models():
    return sorted(
        (m for m in apps.get_models() if m.__module__.startswith("core_apps.") and not m._meta.proxy),
        key=lambda m: m._meta.label_lower,
    )


class SchemaFixtures:
    def __init__(self, origin, image_names):
        self.models = application_models()
        self.number = {m: i + 1 for i, m in enumerate(self.models)}
        self.cache = {}
        self.pending = set()
        self.now = timezone.now()
        self.origin = origin
        self.image_names = image_names

    def image(self, name="apartment.jpg"):
        return f"{self.origin}/media/demo/{name}"

    def get(self, label, key="default", **overrides):
        model = apps.get_model(label)
        tag = (model, key)
        if tag in self.cache:
            return self.cache[tag]
        if tag in self.pending:
            raise ValueError(f"Required relation cycle at {model._meta.label}:{key}; add a scenario override")
        self.pending.add(tag)
        token = f"{model._meta.label_lower}:{key}"
        pk_field = model._meta.pk
        if model._meta.label == "admin_api.PlatformPreferences":
            pk = 1
        elif isinstance(pk_field, models.IntegerField):
            pk = 1000000 + self.number[model] * 10000 + int(hashlib.sha256(key.encode()).hexdigest()[:6], 16) % 9000
        elif isinstance(pk_field, models.UUIDField):
            pk = identity(token)
        else:
            pk = f"demo-{model._meta.model_name}-{key}"[:pk_field.max_length or 100]
        existing = model._base_manager.filter(pk=pk).first()
        if existing:
            self.pending.remove(tag)
            self.cache[tag] = existing
            return existing
        values = {pk_field.attname: pk}
        for field in model._meta.fields:
            if field.primary_key:
                continue
            if field.name in overrides:
                values[field.name] = overrides[field.name]
            elif field.is_relation:
                if field.null:
                    values[field.name] = None
                elif field.related_model is ContentType:
                    values[field.name] = ContentType.objects.get_for_model(apps.get_model("properties.Property"))
                else:
                    values[field.name] = self.get(field.related_model._meta.label)
            else:
                values[field.name] = self.value(field, token)
        obj = model(**values)
        self.specialize(obj, key)
        for name, value in overrides.items():
            setattr(obj, name, value)
        # Validate field types/choices and actual SQL constraints before insertion.
        # clean() is workflow-specific; baseline rows do not assert workflow completion.
        for field in model._meta.fields:
            if not field.is_relation:
                value = getattr(obj, field.attname)
                if value not in (None, "", {}, []):
                    field.clean(value, obj)
        obj.validate_constraints()
        model._base_manager.bulk_create([obj])
        self.pending.remove(tag)
        self.cache[tag] = obj
        return obj

    def value(self, field, token):
        name = field.name
        salt = f"{token}:{name}"
        if isinstance(field, models.UUIDField):
            return identity(salt)
        if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
            return self.now
        if field.has_default():
            return field.get_default()
        if field.null:
            return None
        if field.choices:
            return next(value for value, _ in field.flatchoices if value not in (None, ""))
        if isinstance(field, models.DateTimeField):
            end = any(word in name for word in ("end", "until", "expire", "close", "review_at", "due"))
            return self.now + timedelta(days=90 if end else -7)
        if isinstance(field, models.DateField):
            end = any(word in name for word in ("end", "until", "expire"))
            return self.now.date() + timedelta(days=90 if end else -7)
        if isinstance(field, models.TimeField):
            return time(16, 0)
        if isinstance(field, models.BooleanField):
            return False
        if isinstance(field, models.DecimalField):
            return Decimal("1")
        if isinstance(field, models.IntegerField):
            return 1
        if isinstance(field, models.JSONField):
            return {"demo": True}
        if isinstance(field, models.BinaryField):
            return b"SUKOON SYNTHETIC DEMO - NOT A REAL DOCUMENT"
        if isinstance(field, models.FileField):
            return self.image_names[0]
        if isinstance(field, models.GenericIPAddressField):
            return "127.0.0.1"
        value = f"demo-{hashlib.sha256(salt.encode()).hexdigest()[:12]}"
        if "email" in name:
            value = f"{value}@example.test"
        elif "url" in name or name in ("image", "avatar", "banner", "main_image", "thumbnail_url"):
            value = self.image()
        elif name in ("title", "name", "display_name", "label"):
            value = f"Demo {field.model._meta.verbose_name}"
        elif isinstance(field, models.TextField):
            value = "Synthetic Sukoon demo data for local development. No real agreement, identity or payment."
        return value[:field.max_length] if field.max_length else value

    def specialize(self, obj, key):
        """Explicit relational and constraint policies that reflection cannot infer."""
        label = obj._meta.label
        user = lambda role: self.get("users.User", role)
        if label == "users.User":
            obj.email = f"demo-{key}@example.test"
            obj.first_name, obj.last_name = "Demo", key.replace("-", " ").title()
            obj.set_unusable_password()
            obj.is_verified = obj.is_email_verified = True
            obj.is_staff = obj.is_superuser = False
        if label in ("properties.PortfolioChangeSet", "properties.ResidentialMedia"):
            obj.building = self.get("properties.ResidentialBuilding")
        if label == "properties.PropertyVisitDecision":
            obj.attended, obj.value, obj.reason = True, "proceed", ""
        if label == "properties.Property":
            obj.owner = user("owner")
            obj.main_image = self.image()
            obj.title = "Demo apartment in Maadi"
            obj.status, obj.is_verified = "verified", True
            obj.price, obj.area = Decimal("8500"), 110
            obj.district = "Maadi"
        if label == "profiles.Profile":
            obj.avatar = self.image("studio.jpg")
        if label == "features.Lease":
            obj.owner, obj.tenant = user("owner"), user("tenant")
            obj.renter_company = None
        if label == "features.CompanyLeaseBinding":
            obj.renter_company = self.get("features.Company")
        if label == "features.LeaseResponsibilityTransition":
            obj.previous_owner, obj.next_owner = user("owner"), user("second-owner")
        if label == "features.TenancyInvitation":
            obj.owner, obj.tenant = user("owner"), user("tenant")
        if label == "features.RoommateConnection":
            a, b = user("student"), user("housemate")
            obj.first, obj.second = sorted([a, b], key=lambda u: u.pk)
        if label == "features.RentalSummaryGrant":
            obj.granted_by, obj.recipient = user("tenant"), user("housemate")
        if label == "features.RentalVerificationClaim":
            obj.subject_kind = "identity"
            obj.kyc_submission = self.get("admin_api.KYCSubmission")
        if label == "features.ReviewCase":
            obj.party_a, obj.party_b = user("tenant"), user("owner")
        if label == "features.ReviewOpportunity":
            obj.reviewer = user("tenant")
        if label == "features.CompanySavedItem":
            obj.property = self.get("properties.Property")
        if label == "features.EntitlementGrant":
            obj.user = user("tenant")
        if label == "virtual_tours.PropertyVirtualTour":
            obj.property = self.get("properties.Property")
        if label == "features.RentInvoice":
            obj.lease, obj.purpose = self.get("features.Lease"), "rent"
        if label == "features.RentalEvidence":
            obj.lease, obj.purpose = self.get("features.Lease"), "rental"
        if label == "features.ReservationHold":
            obj.blocked_until_exclusive = obj.ends_on_exclusive
        if label in ("features.SubscriptionPlan", "features.PromotionOption"):
            obj.currency, obj.exponent = "EGP", 2
        if label == "features.SubscriptionPlan":
            obj.amount_minor = 9900
        if label == "features.CompanyMandate":
            obj.limit_minor = 1000000
        if label == "common.ContentView":
            obj.object_id = self.get("properties.Property").pk
        if label == "notifications.DeviceToken":
            obj.token, obj.is_active = f"demo-inert-{key}", False
        if label == "chat.ChatAttachment":
            obj.storage_key = self.image_names[0]
            obj.mime_type = "image/jpeg"
        if label == "advertising.AdvertisementMedia":
            obj.banner, obj.content_type = self.image_names[0], "image/jpeg"
        if label == "support.TicketAttachment":
            # Private identity/document records stay synthetic, never realistic IDs.
            for name in ("storage_key", "file"):
                if hasattr(obj, name):
                    setattr(obj, name, self.image_names[0])
