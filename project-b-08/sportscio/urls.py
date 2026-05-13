# Description: URL routing for the Sportscio Django app, mapping URL patterns to corresponding view functions for handling requests related to user profiles, events, announcements, and administrative actions.

from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("whoami/", views.whoami_view, name="whoami"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("members/", views.members_view, name="members"),
    path("documents/", views.documents_view, name="documents"),
    path("profile/", views.profile_settings_view, name="profile_settings"),
    path("cio/", views.cio_profile_view, name="cio_profile"),
    path("user/", views.user_profile_view, name="user_profile"),
    path("exec/", views.exec_profile_view, name="exec_profile"),
    path("admin/", views.admin_profile_view, name="admin_profile"),
    path("user-roles/", views.user_role_admin_view, name="user_role_admin"),
    path("messages/", views.messages_view, name="messages"),
    path("messages/admin/", views.messages_admin_view, name="messages_admin"),
    path("announcements/", views.announcements_view, name="announcements"),
    path("api/announcements/create/", views.create_announcement, name="create_announcement"),
    path("api/announcements/", views.get_announcements, name="get_announcements"),
    path("exec/new-event/", views.new_event_view, name="new_event"),
    path("events/<int:event_id>/edit/", views.event_edit_view, name="event_edit"),
    path("events/<int:event_id>/delete/", views.event_delete_view, name="event_delete"),
    path("announcements/<int:announcement_id>/edit/", views.announcement_edit_view, name="announcement_edit"),
    path("announcements/<int:announcement_id>/delete/", views.announcement_delete_view, name="announcement_delete"),
    path("documents/<int:document_id>/edit/", views.document_edit_view, name="document_edit"),
    path("documents/<int:document_id>/delete/", views.document_delete_view, name="document_delete"),
]
