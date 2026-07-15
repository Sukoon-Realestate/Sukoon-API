import uuid
import pytest
from django.contrib.contenttypes.models import ContentType
from core_apps.common.models import TimeStampedModel, ContentView


@pytest.mark.django_db
class TestTimeStampedModel:
    def test_abstract_model_fields_present_on_concrete_subclass(self, user):
        profile = user.profile
        assert isinstance(profile.id, uuid.UUID)
        assert isinstance(profile.pkid, int)
        assert profile.created_at is not None
        assert profile.updated_at is not None

    def test_default_ordering_is_by_created_at_desc(self):
        assert TimeStampedModel._meta.ordering == ["-created_at", "-updated_at"]


@pytest.mark.django_db
class TestContentView:
    def test_record_view_creates_entry(self, user):
        """
        Bug: record_view uses wrong field for object_id (content_type.pkid instead
        of content_object.pkid) and uses variable keys in defaults dict.
        This test documents expected behavior.
        """
        profile = user.profile
        ContentView.record_view(
            content_object=profile,
            user=user,
            viewer_ip="127.0.0.1",
        )
        content_type = ContentType.objects.get_for_model(profile)
        assert ContentView.objects.filter(
            content_type=content_type,
            object_id=profile.pkid,
        ).exists()
