from rest_framework import permissions
from apps.projects.models import ProjectMember


class IsProjectMember(permissions.BasePermission):
    """User must be a member of the project to access its resources."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        project_id = getattr(obj, "project_id", None) or getattr(obj, "id", None)
        if hasattr(obj, "project_id"):
            project_id = obj.project_id
        return ProjectMember.objects.filter(project_id=project_id, user=request.user).exists() or obj.owner_id == request.user.id if hasattr(obj, "owner_id") else True


class RolePermission(permissions.BasePermission):
    """Role-based access control via view.required_roles tuple."""

    def has_permission(self, request, view):
        required = getattr(view, "required_roles", None)
        if not required:
            return True
        return request.user.is_authenticated and request.user.role in required
