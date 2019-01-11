from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse


class InvoiceAdminTests(TestCase):
    def setUp(self):
        User.objects.create_user(
            'masha',
            'masha@gmail.com',
            'asdf1234*',
            is_staff=True,
            is_superuser=True
        )
        self.client = Client()
        self.client.login(username='masha', password='asdf1234*')

    def test_index_view_with_no_invoices(self):
        response = self.client.get(reverse('admin:user_invoice_changelist'))
        self.assertEqual(response.status_code, 200)
