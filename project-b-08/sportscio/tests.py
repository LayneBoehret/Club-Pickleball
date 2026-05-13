# Description: Unit tests for user role management functionality in the Sportscio Django app, ensuring that User Admins can only manage roles as specified and are restricted from accessing profile settings.

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile

class UserAdministratorRoleManagementTests(TestCase):
    def setUp(self):
        self.user_admin = User.objects.create_user("useradmin", password="password")
        self.user_admin.profile.role = Profile.ROLE_USER_ADMIN
        self.user_admin.profile.save(update_fields=["role"])

        self.club_leader = User.objects.create_user("leader", password="password")
        self.club_leader.profile.role = Profile.ROLE_OFFICER
        self.club_leader.profile.save(update_fields=["role"])

        self.member = User.objects.create_user("member", password="password")

    def test_user_admin_can_access_role_management(self):
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("user_role_admin"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User role management")

    def test_user_admin_can_change_member_to_club_leader(self):
        self.client.force_login(self.user_admin)
        response = self.client.post(
            reverse("user_role_admin"),
            {"user_id": self.member.id, "new_role": Profile.ROLE_OFFICER},
            follow=True,
        )
        self.member.profile.refresh_from_db()
        self.assertEqual(self.member.profile.role, Profile.ROLE_OFFICER)
        self.assertContains(response, "Updated member to Club leader.")

    def test_user_admin_can_change_club_leader_to_member(self):
        self.client.force_login(self.user_admin)
        response = self.client.post(
            reverse("user_role_admin"),
            {"user_id": self.club_leader.id, "new_role": Profile.ROLE_MEMBER},
            follow=True,
        )
        self.club_leader.profile.refresh_from_db()
        self.assertEqual(self.club_leader.profile.role, Profile.ROLE_MEMBER)
        self.assertContains(response, "Updated leader to Member.")

    def test_user_admin_cannot_assign_user_admin_role(self):
        self.client.force_login(self.user_admin)
        response = self.client.post(
            reverse("user_role_admin"),
            {"user_id": self.member.id, "new_role": Profile.ROLE_USER_ADMIN},
            follow=True,
        )
        self.member.profile.refresh_from_db()
        self.assertEqual(self.member.profile.role, Profile.ROLE_MEMBER)
        self.assertContains(response, "Invalid role change.")

    def test_user_admin_cannot_change_another_user_admin(self):
        self.client.force_login(self.user_admin)
        response = self.client.post(
            reverse("user_role_admin"),
            {"user_id": self.user_admin.id, "new_role": Profile.ROLE_MEMBER},
            follow=True,
        )
        self.user_admin.profile.refresh_from_db()
        self.assertEqual(self.user_admin.profile.role, Profile.ROLE_USER_ADMIN)
        self.assertContains(
            response,
            "User administrator accounts cannot be changed in the application.",
        )

    def test_user_admin_cannot_access_profile_settings(self):
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse("profile_settings"), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("user_role_admin"))
