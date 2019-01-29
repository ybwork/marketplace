import decimal
import json
import requests

from django.shortcuts import redirect

from mysite.settings import API_KEY

from deal.exceptions import InternalServerError, UnauthorizedError, \
    NotFoundError, OtherStatusCodes, NotEnoughMoney, BadRequestError


def get_balance_user(invoice):
    req = requests.get(
        'http://127.0.0.1:5000/v1/invoices/{invoice}/balances'.format(
            invoice=invoice
        ),
        json={
            'api_key': API_KEY,
        }
    )
    check_status_code(req.status_code)
    return decimal.Decimal(
        json.loads(req.content)['balance']
    )


def check_status_code(status_code):
    if status_code == 200:
        return True

    if status_code == 400:
        raise BadRequestError()

    if status_code == 401:
        raise UnauthorizedError()

    if status_code == 404:
        raise NotFoundError()

    if status_code == 500:
        raise InternalServerError()

    raise OtherStatusCodes()


def check_user_balance(invoice, amount_money_payment):
    balance = get_balance_user(invoice)
    if balance < amount_money_payment:
        raise NotEnoughMoney()


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
    return check_status_code(req.status_code)


def confirm_payment(invoice, code_confirm):
    req = requests.post(
        'http://127.0.0.1:5000/v1/payments/confirm',
        json={
            'api_key': API_KEY,
            'invoice': invoice,
            'code_confirm': code_confirm
        }
    )
    check_status_code(req.status_code)
    return json.loads(req.content)['key']


def available_request_methods(http_methods=[]):
    def decorator(function_to_decorate):
        def original(self, request, *args, **kwargs):
            if request.method not in http_methods:
                return redirect(request.META['HTTP_REFERER'])
            return function_to_decorate(self, request, *args, **kwargs)
        return original
    return decorator
