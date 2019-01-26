import decimal
import json
import requests
from django.shortcuts import redirect

from mysite.settings import API_KEY


def get_user_balance(invoice):
    balance = requests.get(
        'http://127.0.0.1:5000/v1/invoices/{invoice}/balances'.format(
            invoice=invoice
        ),
        json={
            'api_key': API_KEY,
            'invoice': str(invoice)
        }
    )
    decoded_balance = json.loads(balance.content)['balance']
    return decimal.Decimal(decoded_balance)


def send_code_confirm_payment(amount_money, invoice_provider, invoice_reciever):
    code_confirm = requests.post(
        'http://127.0.0.1:5000/v1/payments',
        json={
            'api_key': API_KEY,
            'amount_money': amount_money,
            'invoice_provider': invoice_provider,
            'invoice_reciever': invoice_reciever
        }
    )
    return json.loads(code_confirm)


def is_enough_user_balance(invoice, payment_amount):
    """
    Сравнивает текущий баланс пользователя с суммой, которую он хочет
    заплатить.
    """
    buyer_balance = get_user_balance(
        invoice=invoice
    )
    return buyer_balance > payment_amount


def available_request_methods(http_methods=[]):
    def decorator(function_to_decorate):
        def original(self, request, *args, **kwargs):
            if request.method not in http_methods:
                return redirect(request.META['HTTP_REFERER'])
            return function_to_decorate(self, request, *args, **kwargs)
        return original
    return decorator

