import decimal
import json
import requests
from django.contrib import messages

from django.shortcuts import redirect, render

from mysite.settings import API_KEY

from deal.exceptions import InternalServerError, UnauthorizedError, \
    NotFoundError, OtherStatusCodes, NotEnoughMoney, BadRequestError

from mysite.settings import API_DOMEN


def handle_api_response(function_to_decorate):
    def original(self, request, *args, **kwargs):
        try:
            return function_to_decorate(self, request, *args, **kwargs)
        except (
            NotEnoughMoney,
            NotFoundError,
            BadRequestError
        ) as error:
            return self.redirect_with_message(
                request=request,
                message=str(error),
                type_message=messages.WARNING,
                redirect_to=request.META['HTTP_REFERER']
            )
        except (
            requests.exceptions.ConnectionError,
            InternalServerError,
            UnauthorizedError,
            OtherStatusCodes
        ):
            return render(
                request=request,
                template_name='errors/500.html'
            )
    return original


def get_balance_user(invoice):
    response = send_request(
        url='/v1/invoices/{invoice}/balances'.format(invoice=invoice),
        method='get',
        params={
            'api_key': API_KEY,
        }
    )
    return decimal.Decimal(response['balance'])


def send_request(url, method, params):
    req = getattr(requests, method)(
        '{domen}{url}'.format(domen=API_DOMEN, url=url),
        json=params
    )
    check_status_code(status_code=req.status_code)
    return parse_response(response=req.content)


def check_status_code(status_code):
    if status_code == 200:
        return True

    if status_code == 400:
        raise BadRequestError('Отсутствуют параметры запроса')

    if status_code == 401:
        raise UnauthorizedError('Не авторизован')

    if status_code == 404:
        raise NotFoundError('Объект не найден')

    if status_code == 500:
        raise InternalServerError('Что то пошло не так, попробуйте позже')

    raise OtherStatusCodes()


def parse_response(response):
    return json.loads(response)


def check_user_balance(invoice, amount_money_payment):
    balance = get_balance_user(invoice)
    if balance < amount_money_payment:
        raise NotEnoughMoney('Не хватает денег на счете')


def pay(amount_money, number_invoice_provider, number_invoice_reciever):
    return send_request(
        url='/v1/payments',
        method='post',
        params={
            'api_key': API_KEY,
            'amount_money': str(amount_money),
            'number_invoice_provider': number_invoice_provider,
            'number_invoice_reciever': number_invoice_reciever
        }
    )


def confirm_payment(invoice, code_confirm):
    response = send_request(
        url='/v1/payments/confirm',
        method='post',
        params={
            'api_key': API_KEY,
            'invoice': invoice,
            'code_confirm': code_confirm
        }
    )
    return response['key']


def perform_payment(key):
    return send_request(
        url='/v1/payments/perform',
        method='post',
        params={
            'api_key': API_KEY,
            'key': key
        }
    )


def available_request_methods(http_methods=[]):
    def decorator(function_to_decorate):
        def original(self, request, *args, **kwargs):
            if request.method not in http_methods:
                return redirect(request.META['HTTP_REFERER'])
            return function_to_decorate(self, request, *args, **kwargs)
        return original
    return decorator

