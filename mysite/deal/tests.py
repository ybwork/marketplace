from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client

from deal.models import Offer


class OfferAdminTests(TestCase):
    def setUp(self):
        pass

    def test_save_offer_with_current_user(self):
        pass

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
