from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import SupportMessage, SupportTicket


User = get_user_model()


class Stage19SupportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="support-user", password="pass12345")
        self.client.force_login(self.user)

    def test_user_can_create_ticket(self):
        response = self.client.post(
            "/account/support/new/",
            {"subject": "Order problem", "category": "order", "order_number": "AV-42", "body": "Please check this order."},
        )
        self.assertEqual(response.status_code, 302)
        ticket = SupportTicket.objects.get(user=self.user)
        self.assertEqual(ticket.status, SupportTicket.Status.WAITING_SUPPORT)
        self.assertEqual(ticket.messages.count(), 1)

    def test_user_cannot_open_another_users_ticket(self):
        other = User.objects.create_user(username="other", password="pass12345")
        ticket = SupportTicket.objects.create(user=other, subject="Private")
        SupportMessage.objects.create(ticket=ticket, sender=other, body="secret")
        response = self.client.get(f"/account/support/{ticket.reference}/")
        self.assertEqual(response.status_code, 404)
