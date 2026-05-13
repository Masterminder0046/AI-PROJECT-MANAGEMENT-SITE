from django.db import models


class AnalyticsSnapshot(models.Model):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="snapshots")
    captured_at = models.DateTimeField(auto_now_add=True, db_index=True)
    metrics = models.JSONField(default=dict)

    class Meta:
        ordering = ["-captured_at"]
