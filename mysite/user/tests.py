from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from user.models import Invoice


class InvoiceAdminTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
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

    def test_save_invoice_with_current_user(self):
        response = self.client.post(reverse('admin:user_invoice_add'), {'num': 'x23md'})
        self.assertEqual(Invoice.objects.last().user, response.wsgi_request.user)
