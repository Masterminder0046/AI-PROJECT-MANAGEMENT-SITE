from django.db import models
from django.conf import settings


class AIRequest(models.Model):
    class Kind(models.TextChoices):
        SUBTASKS = "subtasks", "Generate subtasks"
        PLAN = "plan", "Plan project"
        SUGGEST = "suggest", "Suggest"
        ESTIMATE = "estimate", "Estimate"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    prompt = models.TextField()
    response = models.JSONField(default=dict, blank=True)
    tokens_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
