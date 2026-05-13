from apps.projects.models import ActivityLog
from services.task_services import broadcast_task_event

def log_activity(project_id, actor, verb, payload=None):
    """
    Log an activity for a project and broadcast it via WebSocket.
    """
    activity = ActivityLog.objects.create(
        project_id=project_id,
        actor=actor,
        verb=verb,
        payload=payload or {}
    )
    
    # Broadcast to the project group so the activity feed updates in real-time
    broadcast_task_event(project_id, "activity.created", {
        "id": activity.id,
        "actor": actor.email if actor else "System",
        "verb": verb,
        "payload": payload,
        "created_at": activity.created_at.isoformat()
    })
    
    return activity
