from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.projects.models import Project, ProjectMember, ActivityLog
from apps.tasks.models import Task, Comment, Attachment, TaskDependency
from apps.notifications.models import Notification
from apps.ai_engine.models import AIRequest

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username", "first_name", "last_name", "role", "avatar", "bio", "is_online", "last_seen"]
        read_only_fields = ["id", "is_online", "last_seen"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "username", "password", "first_name", "last_name"]

    def create(self, validated):
        return User.objects.create_user(**validated)


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = ["id", "user", "role", "invited_at"]


class ProjectSerializer(serializers.ModelSerializer):
    members = ProjectMemberSerializer(many=True, read_only=True)
    owner = UserSerializer(read_only=True)
    task_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Project
        fields = ["id", "name", "slug", "description", "color", "status", "owner", "members", "task_count", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ["id", "task", "author", "body", "created_at"]
        read_only_fields = ["id", "author", "created_at"]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id", "task", "file", "filename", "size", "content_type", "created_at"]
        read_only_fields = ["id", "filename", "size", "content_type", "created_at"]


class TaskSerializer(serializers.ModelSerializer):
    assignees = UserSerializer(many=True, read_only=True)
    assignee_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=User.objects.all(), source="assignees", required=False
    )
    subtasks = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = ["id", "project", "parent", "title", "description", "status", "priority",
                  "assignees", "assignee_ids", "reporter", "due_date", "labels", "order",
                  "is_recurring", "recurrence", "ai_generated", "subtasks", "comments",
                  "attachments", "created_at", "updated_at"]
        read_only_fields = ["id", "reporter", "ai_generated", "created_at", "updated_at"]

    def get_subtasks(self, obj):
        return TaskSerializer(obj.subtasks.all(), many=True).data if obj.parent_id is None else []


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    class Meta:
        model = Notification
        fields = ["id", "kind", "title", "body", "url", "is_read", "actor", "created_at"]


class AIRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRequest
        fields = ["id", "kind", "prompt", "response", "tokens_used", "created_at"]
        read_only_fields = ["id", "response", "tokens_used", "created_at"]
