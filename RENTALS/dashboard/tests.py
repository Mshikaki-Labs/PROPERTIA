from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class DashboardViewTests(TestCase):
    def test_dashboard_loads_for_logged_in_user(self):
        user = User.objects.create_user(username='dashboard-user', password='pass12345')
        self.client.login(username='dashboard-user', password='pass12345')

        response = self.client.get(reverse('dashboard_home'))

        self.assertEqual(response.status_code, 200)
