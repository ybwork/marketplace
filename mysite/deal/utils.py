import decimal
import json
import requests

from mysite.settings import API_KEY
from django.shortcuts import redirect


class UnauthorizedError(Exception):
    pass


class InternalServerError(Exception):
    pass


class NotFoundError(Exception):
    pass


class OtherStatusCodes(Exception):
    pass


def get_balance_user(invoice):
    req = requests.get(
        'http://127.0.0.1:5000/v1/invoices/{invoice}/balances'.format(
            invoice=invoice
        ),
        json={
            'api_key': API_KEY,
            'invoice': str(invoice)
        }
    )

    if req.status_code == 500:
        raise InternalServerError()

    if req.status_code == 401:
        raise UnauthorizedError()

    if req.status_code == 404:
        raise NotFoundError()

    if req.status_code == 200:
        return decimal.Decimal(
            json.loads(req.content)['balance']
        )

    raise OtherStatusCodes()


def pay(amount_money, number_invoice_provider, number_invoice_reciever):
    req = requests.post(
        'http://127.0.0.1:5000/v1/payments',
        json={
            'api_key': API_KEY,
            'amount_money': str(amount_money),
            'number_invoice_provider': number_invoice_provider,
            'number_invoice_reciever': number_invoice_reciever
        }
    )

    if req.status_code == 500:
        raise InternalServerError()

    if req.status_code == 401:
        raise UnauthorizedError()

    if req.status_code == 404:
        raise NotFoundError()

    if req.status_code == 200:
        return True

    raise OtherStatusCodes()


def confirm_payment():
    pass


def available_request_methods(http_methods=[]):
    def decorator(function_to_decorate):
        def original(self, request, *args, **kwargs):
            if request.method not in http_methods:
                return redirect(request.META['HTTP_REFERER'])
            return function_to_decorate(self, request, *args, **kwargs)
        return original
    return decorator

