from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from user.models import Invoice


class InvoiceAdminTests(TestCase):
    def setUp(self):
        User.objects.create_user(
            username='admin',
            email='admin@gmail.com',
            password='asdf1234@',
            is_staff=True,
            is_superuser=True
        )

        user = User.objects.create_user(
            username='mike',
            email='mike@gmail.com',
            password='asdf1234~',
            is_staff=True,
        )
        permission = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(Invoice)
        ).filter(codename__in=['add_invoice', 'view_invoice'])
        user.user_permissions.set(permission)

        self.client = Client()

    def test_save_invoice_with_current_user(self):
        self.client.login(username='mike', password='asdf1234~')
        response = self.client.post(reverse('admin:user_invoice_add'), {'num': 'x23md'})
        self.assertEqual(Invoice.objects.last().user, response.wsgi_request.user)

    # def test_superuser_sees_all_invoices(self):
    #     response = self.client.get(reverse('admin:user_invoice_changelist'))
    #     print(response.context)
