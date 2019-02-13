from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from user.admin import InvoiceAdmin

from user.models import Invoice


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
    #
    # def test_index_view_with_no_invoices(self):
    #     response = self.client.get(reverse('admin:user_invoice_changelist'))
    #     self.assertEqual(response.status_code, 200)

    def test_save_model(self):
        model_admin = InvoiceAdmin(model=Invoice, admin_site=AdminSite())
        result = model_admin.save_model(request=None, obj=Invoice(user=User.objects.first(), num='dfdfdf'), form=None, change=None)
        print(result)
