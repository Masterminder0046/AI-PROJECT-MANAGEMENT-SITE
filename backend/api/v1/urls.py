from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.v1.views import (
    RegisterView, LogoutView, MeView, UserViewSet, ProjectViewSet, TaskViewSet,
    AttachmentViewSet, NotificationViewSet, AnalyticsView, AIView, GlobalSearchView,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"projects", ProjectViewSet, basename="projects")
router.register(r"tasks", TaskViewSet, basename="tasks")
router.register(r"attachments", AttachmentViewSet, basename="attachments")
router.register(r"notifications", NotificationViewSet, basename="notifications")

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/",    TokenObtainPairView.as_view()),
    path("auth/refresh/",  TokenRefreshView.as_view()),
    path("auth/logout/",   LogoutView.as_view()),
    path("auth/google/",   include("dj_rest_auth.registration.urls")),
    path("auth/",          include("dj_rest_auth.urls")),
    path("auth/me/",       MeView.as_view()),
    path("analytics/",     AnalyticsView.as_view()),
    path("ai/",            AIView.as_view()),
    path("search/",        GlobalSearchView.as_view()),
    path("", include(router.urls)),
]
