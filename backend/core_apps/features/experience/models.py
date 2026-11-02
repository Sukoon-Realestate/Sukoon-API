import uuid

from django.conf import settings
from django.db import models


class ExperiencePreferences(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    scope = models.CharField(max_length=100)
    revision = models.PositiveIntegerField(default=0)
    content = models.JSONField(default=dict)
    tombstones = models.JSONField(default=dict)
    conflicts = models.JSONField(default=dict)
    ranking = models.JSONField(default=dict)
    behavioral_consent = models.BooleanField(default=False)
    suggestion_push = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'scope'], name='experience_account_scope')]


class ExperienceVersion(models.Model):
    preferences = models.ForeignKey(ExperiencePreferences, on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    content = models.JSONField(default=dict)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['preferences', 'revision'], name='experience_version')]


class ExperienceOperation(models.Model):
    preferences = models.ForeignKey(ExperiencePreferences, on_delete=models.CASCADE)
    operation_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['preferences', 'operation_id'], name='experience_operation')]


class DiscoveryInteraction(models.Model):
    preferences = models.ForeignKey(ExperiencePreferences, on_delete=models.CASCADE)
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE)
    offer_id = models.CharField(max_length=64, blank=True)
    kind = models.CharField(max_length=16)
    day = models.DateField()
    class Meta:
        constraints = [models.UniqueConstraint(fields=['preferences', 'property', 'offer_id', 'kind', 'day'], name='experience_daily_signal')]
        indexes = [models.Index(fields=['day'], name='experience_signal_age')]


class PreparationTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey('features.HousingGroup', on_delete=models.CASCADE, null=True)
    company_request = models.ForeignKey('features.CompanyHousingRequest', on_delete=models.CASCADE, null=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    membership_period = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    due_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=16, default='todo')
    revision = models.PositiveIntegerField(default=1)
    history = models.JSONField(default=list)
    operations = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.CheckConstraint(
            check=(models.Q(group__isnull=False, company_request__isnull=True) | models.Q(group__isnull=True, company_request__isnull=False)),
            name='experience_task_one_context',
        )]
        indexes = [models.Index(fields=['assignee', 'status', 'due_at'], name='experience_task_due')]


class ExperienceDismissal(models.Model):
    preferences = models.ForeignKey(ExperiencePreferences, on_delete=models.CASCADE)
    identity = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['preferences', 'identity'], name='experience_dismissal')]


class ListingAssessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    operation_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    snapshot = models.JSONField(default=dict)
    batches = models.JSONField(default=list)
    status = models.CharField(max_length=16, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    class Meta:
        constraints = [models.UniqueConstraint(fields=['owner', 'operation_id'], name='experience_assessment_operation')]
