from django.db import models
from django.conf import settings


class Notification(models.Model):
    class Kind(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        MENTIONED = "mentioned", "Mentioned"
        COMMENT = "comment", "Comment"
        DUE = "due", "Due Soon"
        STATUS = "status", "Status Changed"
        SYSTEM = "system", "System"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.SYSTEM)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    url = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["recipient", "is_read", "-created_at"])]
        ordering = ["-created_at"]
