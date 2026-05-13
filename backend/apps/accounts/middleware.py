"""Audit logging middleware — records mutating requests."""
from .models import AuditLog


class AuditLogMiddleware:
    SAFE = {"GET", "HEAD", "OPTIONS"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            if request.method not in self.SAFE and request.path.startswith("/api/"):
                user = getattr(request, "user", None)
                AuditLog.objects.create(
                    actor=user if getattr(user, "is_authenticated", False) else None,
                    action=f"{request.method} {request.path}",
                    ip=request.META.get("REMOTE_ADDR"),
                    metadata={"status": response.status_code},
                )
        except Exception:
            pass
        return response
