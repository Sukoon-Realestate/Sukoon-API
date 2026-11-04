"""Only measured listing interest. Missing attribution is never a zero."""
from django.contrib.contenttypes.models import ContentType
from core_apps.common.models import ContentView
from ..models import Property


def listing_funnel(prop, cutoff):
    views = ContentView.objects.filter(content_type=ContentType.objects.get_for_model(Property),
        object_id=prop.pk).exclude(user_id=prop.owner_id)
    visits = prop.visits.filter(context_kind='personal', renter_workspace='individual',
        company__isnull=True, academic_plan__isnull=True)
    if cutoff:
        views = views.filter(last_viewed__gte=cutoff)
        visits = visits.filter(created_at__gte=cutoff)
    return {'protocol': 1, 'scope': 'property', 'period_start': cutoff.isoformat() if cutoff else None,
        'stages': [
            {'kind': 'views', 'count': views.count(), 'definition': 'unique_recorded_viewers_last_seen_in_period'},
            # The existing chat context can bind several properties but has no
            # per-property contact timestamp. Its creation time cannot stand in.
            {'kind': 'contacts', 'count': None, 'definition': 'unavailable_per_listing_contact_attribution'},
            {'kind': 'viewing_requests', 'count': visits.count(), 'definition': 'individual_viewing_requests_created_in_period'},
        ], 'rates': None, 'suggestions': ['listing_information', 'listing_photos']}
