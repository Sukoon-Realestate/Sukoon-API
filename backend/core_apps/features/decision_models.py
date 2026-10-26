"""Private account notes. Deliberately absent from staff/admin read APIs."""

import uuid
from django.conf import settings
from django.db import models


class DecisionNotebook(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    workspace = models.CharField(max_length=16)
    company_context = models.CharField(max_length=36, blank=True)
    revision = models.PositiveIntegerField(default=0)
    content = models.JSONField(default=dict)
    tombstones = models.JSONField(default=dict)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["user", "workspace", "company_context"],
            name="decision_notebook_account_context",
        )]


class DecisionNotebookVersion(models.Model):
    notebook = models.ForeignKey(DecisionNotebook, on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    content = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["notebook", "revision"], name="decision_notebook_version",
        )]


class DecisionNotebookConflict(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notebook = models.ForeignKey(DecisionNotebook, on_delete=models.CASCADE)
    record_key = models.TextField()
    base = models.JSONField(null=True)
    current = models.JSONField(null=True)
    incoming = models.JSONField(null=True)
    fields = models.JSONField(default=list)
    revision = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True)
    resolution = models.CharField(max_length=16, blank=True)


class DecisionNotebookOperation(models.Model):
    notebook = models.ForeignKey(DecisionNotebook, on_delete=models.CASCADE)
    operation_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    revision = models.PositiveIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["notebook", "operation_id"], name="decision_notebook_operation",
        )]
