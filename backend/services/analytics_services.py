from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from apps.projects.models import Project
from apps.tasks.models import Task


def project_metrics(project_id):
    qs = Task.objects.filter(project_id=project_id)
    total = qs.count()
    by_status = dict(qs.values_list("status").annotate(c=Count("id")))
    overdue = qs.filter(due_date__lt=timezone.now()).exclude(status="completed").count()
    completion = (by_status.get("completed", 0) / total * 100) if total else 0
    return {
        "total": total,
        "by_status": by_status,
        "overdue": overdue,
        "completion": round(completion, 1),
    }


def team_productivity(user):
    since = timezone.now() - timedelta(days=30)
    completed = Task.objects.filter(assignees=user, status="completed",
                                    updated_at__gte=since).count()
    open_tasks = Task.objects.filter(assignees=user).exclude(status="completed").count()
    by_day = (Task.objects.filter(assignees=user, status="completed", updated_at__gte=since)
              .extra(select={"day": "DATE(updated_at)"})
              .values("day").annotate(c=Count("id")).order_by("day"))
    return {
        "completed_30d": completed,
        "open": open_tasks,
        "completed_by_day": list(by_day),
        "projects": Project.objects.filter(members__user=user).count(),
    }
