from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from user.models import Invoice


class InvoiceAdminTests(TestCase):
    user = {
        'admin': {
            'name': 'admin',
            'email': 'admin@gmail.com',
            'password': 'asdf1234!'
        },
        'user1': {
            'name': 'mike',
            'email': 'mike@gmail.com',
            'password': 'asdf1234@'
        },
        'user2': {
            'name': 'vika',
            'email': 'vika@gmail.com',
            'password': 'asdf1234#'
        }
    }

    def get_user(self, name):
        return self.user[name]

    def setUp(self):
        admin = self.get_user('admin')
        User.objects.create_user(
            username=admin['name'],
            email=admin['email'],
            password=admin['password'],
            is_staff=True,
            is_superuser=True
        )
        user1 = self.get_user('user1')
        user1_obj = User.objects.create_user(
            username=user1['name'],
            email=user1['email'],
            password=user1['password'],
            is_staff=True,
        )
        user2 = self.get_user('user2')
        user2_obj = User.objects.create_user(
            username=user2['name'],
            email=user2['email'],
            password=user2['password'],
            is_staff=True,
        )

        permissions = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(Invoice)
        ).filter(codename__in=['add_invoice', 'view_invoice'])
        user1_obj.user_permissions.set(permissions)
        user2_obj.user_permissions.set(permissions)

        self.user1_obj = user1_obj
        self.user2_obj = user2_obj
        self.client = Client()

    def test_save_invoice_with_current_user(self):
        user = self.get_user('user1')
        self.client.login(username=user['name'], password=user['password'])
        response = self.client.post(reverse('admin:user_invoice_add'), {'num': 'x23md'})
        self.assertEqual(Invoice.objects.last().user, response.wsgi_request.user)

    def test_superuser_sees_all_invoices(self):
        user1 = self.get_user('user1')
        self.client.login(username=user1['name'], password=user1['password'])
        Invoice.objects.bulk_create([
            Invoice(num='aaa', user=self.user1_obj),
            Invoice(num='bbb', user=self.user1_obj)
        ])

        admin = self.get_user('admin')
        self.client.login(username=admin['name'], password=admin['password'])
        response = self.client.get(reverse('admin:user_invoice_changelist'))
        invoice_list = response.context['cl'].queryset
        self.assertQuerysetEqual(invoice_list, ['<Invoice: bbb>', '<Invoice: aaa>'])

    def test_user_sees_only_his_invoice(self):
        user1 = self.get_user('user1')
        self.client.login(username=user1['name'], password=user1['password'])
        Invoice.objects.bulk_create([
            Invoice(num='aaa', user=self.user1_obj),
        ])
        self.client.logout()

        user2 = self.get_user('user2')
        self.client.login(username=user2['name'], password=user2['password'])
        Invoice.objects.bulk_create([
            Invoice(num='bbb', user=self.user2_obj)
        ])

        response = self.client.get(reverse('admin:user_invoice_changelist'))
        invoice_list = response.context['cl'].queryset
        self.assertQuerysetEqual(invoice_list, ['<Invoice: bbb>'])