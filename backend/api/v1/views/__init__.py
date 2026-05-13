from rest_framework import generics, status, viewsets, permissions, decorators, response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from api.v1.serializers import (
    UserSerializer, RegisterSerializer, ProjectSerializer, TaskSerializer,
    CommentSerializer, AttachmentSerializer, NotificationSerializer, AIRequestSerializer,
)
from api.v1.permissions import IsProjectMember, RolePermission
from apps.projects.models import Project, ProjectMember, ActivityLog
from apps.tasks.models import Task, Comment, Attachment
from apps.notifications.models import Notification
from apps.ai_engine.models import AIRequest
from services.ai_services import generate_subtasks, plan_project, suggest_next
from services.notification_services import push_notification
from services.analytics_services import project_metrics, team_productivity
from services.task_services import broadcast_task_event
from services.activity_services import log_activity

User = get_user_model()


# -------- AUTH --------
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    def post(self, request):
        try:
            RefreshToken(request.data["refresh"]).blacklist()
        except Exception:
            pass
        return response.Response(status=204)


class MeView(APIView):
    def get(self, request):
        user = request.user
        if user.is_superuser and user.role != "admin":
            user.role = "admin"
            user.save(update_fields=["role"])
        return response.Response(UserSerializer(user).data)

    def patch(self, request):
        s = UserSerializer(request.user, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return response.Response(s.data)


# -------- USERS --------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    required_roles = ["admin"] # For updates
    filterset_fields = ["role"]
    search_fields = ["email", "username", "first_name", "last_name"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), RolePermission()]

    def perform_update(self, serializer):
        if self.request.user.role != "admin":
            raise permissions.PermissionDenied("Only admins can update user details.")
        serializer.save()


# -------- PROJECTS --------
class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        u = self.request.user
        qs = Project.objects.annotate(task_count=Count("tasks")).order_by("-created_at")
        if u.role == "admin":
            return qs.all()
        return qs.filter(Q(owner=u) | Q(members__user=u)).distinct()

    def perform_update(self, serializer):
        p = self.get_object()
        u = self.request.user
        if u.role not in ["admin", "manager"] and p.owner != u:
            member = p.members.filter(user=u).first()
            if not member or member.role not in ["owner", "manager"]:
                raise permissions.PermissionDenied("You do not have permission to edit this project.")
        serializer.save()

    def perform_destroy(self, instance):
        u = self.request.user
        if u.role not in ["admin", "manager"] and instance.owner != u:
            raise permissions.PermissionDenied("You do not have permission to delete this project.")
        log_activity(instance.id, u, "deleted project", {"name": instance.name})
        instance.delete()

    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)
        ProjectMember.objects.create(project=project, user=self.request.user,
                                     role=ProjectMember.MemberRole.OWNER)
        log_activity(project.id, self.request.user, "created project")

    @decorators.action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        p = self.get_object(); p.status = Project.Status.ARCHIVED; p.save()
        return response.Response(self.get_serializer(p).data)

    @decorators.action(detail=True, methods=["post"], url_path="invite")
    def invite(self, request, pk=None):
        p = self.get_object()
        user = User.objects.filter(email=request.data.get("email")).first()
        if not user:
            return response.Response({"detail": "user not found"}, status=404)
        member, _ = ProjectMember.objects.get_or_create(
            project=p, user=user, defaults={"role": request.data.get("role", "member")}
        )
        push_notification(user, kind="system", title=f"Added to {p.name}", url=f"/project/{p.id}")
        return response.Response({"id": member.id, "user_id": user.id})


# -------- TASKS --------
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    filterset_fields = ["project", "status", "priority", "parent"]
    search_fields = ["title", "description"]

    def get_queryset(self):
        u = self.request.user
        qs = (Task.objects
                .select_related("project", "reporter")
                .prefetch_related("assignees", "subtasks", "comments", "attachments"))
        if u.role == "admin":
            return qs.all().distinct()
        elif u.role == "developer":
            return qs.filter(assignees=u).distinct()
        return qs.filter(Q(project__owner=u) | Q(project__members__user=u)).distinct()

    def perform_create(self, serializer):
        task = serializer.save(reporter=self.request.user)
        broadcast_task_event(task.project_id, "task.created", TaskSerializer(task).data)
        log_activity(task.project_id, self.request.user, "created task", {"title": task.title, "id": task.id})
        for u in task.assignees.all():
            push_notification(u, kind="assigned", title=f"Assigned: {task.title}",
                              url=f"/task/{task.id}", actor=self.request.user)

    def perform_update(self, serializer):
        u = self.request.user
        task = self.get_object()
        if u.role == "developer" and not task.assignees.filter(id=u.id).exists() and task.reporter != u:
            raise permissions.PermissionDenied("Developers can only edit tasks assigned to them.")
        old_status = task.status
        task = serializer.save()
        if old_status != task.status:
            log_activity(task.project_id, u, "moved task", {"title": task.title, "from": old_status, "to": task.status})
        else:
            log_activity(task.project_id, u, "updated task", {"title": task.title})
        broadcast_task_event(task.project_id, "task.updated", TaskSerializer(task).data)

    def perform_destroy(self, instance):
        u = self.request.user
        if u.role == "developer" and instance.reporter != u:
            raise permissions.PermissionDenied("Developers cannot delete tasks.")
        pid = instance.project_id; tid = instance.id
        instance.delete()
        broadcast_task_event(pid, "task.deleted", {"id": tid})

    @decorators.action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        """Body: [{id, status, order}, ...]  — bulk update for kanban DnD."""
        for item in request.data or []:
            Task.objects.filter(id=item["id"]).update(status=item["status"], order=item["order"])
        return response.Response({"ok": True})

    @decorators.action(detail=True, methods=["post"], url_path="comments")
    def add_comment(self, request, pk=None):
        task = self.get_object()
        c = Comment.objects.create(task=task, author=request.user, body=request.data.get("body", ""))
        log_activity(task.project_id, request.user, "commented on task", {"title": task.title})
        broadcast_task_event(task.project_id, "comment.created", CommentSerializer(c).data)
        return response.Response(CommentSerializer(c).data, status=201)


# -------- ATTACHMENTS / UPLOADS --------
class AttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    queryset = Attachment.objects.all()

    ALLOWED = {"image/png", "image/jpeg", "image/webp", "application/pdf",
               "application/zip", "application/msword", "text/plain", "application/json",
               "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    MAX_SIZE = 25 * 1024 * 1024

    def create(self, request, *args, **kwargs):
        f = request.FILES.get("file")
        if not f:
            print("Upload failed: No file")
            return response.Response({"detail": "file required"}, status=400)
        if f.size > self.MAX_SIZE:
            print(f"Upload failed: File too large ({f.size} > {self.MAX_SIZE})")
            return response.Response({"detail": "file too large"}, status=400)
        if f.content_type not in self.ALLOWED:
            print(f"Upload failed: Type {f.content_type} not in allowed: {self.ALLOWED}")
            return response.Response({"detail": f"type {f.content_type} not allowed"}, status=400)
        att = Attachment.objects.create(
            task_id=request.data["task"], uploader=request.user, file=f,
            filename=f.name, size=f.size, content_type=f.content_type,
        )
        return response.Response(AttachmentSerializer(att).data, status=201)


# -------- NOTIFICATIONS --------
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @decorators.action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        n = self.get_object(); n.is_read = True; n.save()
        return response.Response({"ok": True})

    @decorators.action(detail=False, methods=["post"], url_path="read-all")
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return response.Response({"ok": True})


# -------- ANALYTICS --------
class AnalyticsView(APIView):
    def get(self, request):
        project_id = request.query_params.get("project")
        if project_id:
            return response.Response(project_metrics(project_id))
        return response.Response(team_productivity(request.user))


# -------- GLOBAL SEARCH --------
class GlobalSearchView(APIView):
    def get(self, request):
        q = request.query_params.get("q", "")
        if len(q) < 2:
            return response.Response({"projects": [], "tasks": [], "users": []})

        u = request.user
        
        # Projects I am member of
        projects = Project.objects.filter(
            Q(name__icontains=q) | Q(description__icontains=q),
            Q(owner=u) | Q(members__user=u)
        ).distinct()[:10]
        
        # Tasks in those projects
        tasks = Task.objects.filter(
            Q(title__icontains=q) | Q(description__icontains=q),
            Q(project__owner=u) | Q(project__members__user=u)
        ).distinct()[:20]
        
        # Users (limited search)
        users = User.objects.filter(
            Q(email__icontains=q) | Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )[:10]

        return response.Response({
            "projects": ProjectSerializer(projects, many=True).data,
            "tasks": TaskSerializer(tasks, many=True).data,
            "users": UserSerializer(users, many=True).data
        })


# -------- AI ENGINE --------
class AIView(APIView):
    def post(self, request):
        kind = request.data.get("kind", "subtasks")
        prompt = request.data.get("prompt", "")
        context = request.data.get("context", {})
        try:
            if kind == "subtasks":
                data, tokens = generate_subtasks(prompt, context)
            elif kind == "plan":
                data, tokens = plan_project(prompt)
            else:
                data, tokens = suggest_next(prompt, context)
            
            # Save request record
            AIRequest.objects.create(
                user=request.user, kind=kind, prompt=prompt, response=data, tokens_used=tokens
            )
            return response.Response(data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return response.Response({"detail": f"AI error: {str(e)}"}, status=500)
