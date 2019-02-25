from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client

from deal.models import Offer
from django.urls import reverse

from user.models import Invoice


class OfferAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@gmail.com',
            password='asdf!1234',
            is_staff=True,
            is_superuser=True
        )

        self.__user_password = 'asdf@1234'
        self.user = User.objects.create_user(
            username='mike',
            email='mike@gmail.com',
            password=self.__user_password,
            is_staff=True
        )
        permissions = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(Offer)
        ).filter(
            codename__in=['add_offer', 'view_offer']
        )
        self.user.user_permissions.set(permissions)

        self.client = Client()

    def test_save_offer_with_current_user(self):
        self.client.login(
            username=self.user.username,
            password=self.__user_password
        )
        invoice = Invoice.objects.create(
            user=self.user,
            num='z3gl5'
        )
        response = self.client.post(
            reverse('admin:deal_offer_add'),
            {
                'title': 'Offer 1',
                'description': '...',
                'price': '100',
                'limit_hours_on_pay': '1',
                'money_to_invoice': invoice
            }
        )
        self.assertEqual(Offer.objects.last().user, response.wsgi_request.user)
        # print(response.status_code)
        # print(Offer.objects.last())
        # print(response.wsgi_request.user)
        # print(response.wsgi_request.session)

    def test_superuser_sees_all_offers(self):
        pass

    def test_superuser_change_any_offer(self):
        pass

    def test_check_user_on_owner(self):
        pass

    def test_superuser_delete_any_offer(self):
        pass

    def test_show_invoices_only_current_user_in_field_money_to_invoice(self):
        pass

    def test_extra_context_for_change_view(self):
        pass
