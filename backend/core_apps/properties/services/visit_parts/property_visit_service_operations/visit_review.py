"""Legacy review writes require the explicit immutable confirmation flow."""
from core_apps.features.services.reputation.policy import ReviewError

class VisitReviewMixin:
    @classmethod
    def create_review(cls, tenant, visit_obj, validated_data):
        raise ReviewError("client_update_required")
