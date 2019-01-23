import decimal
import json
import requests

from mysite.settings import API_KEY


def get_user_balance(invoice):
    balance = requests.get(
        'http://127.0.0.1:5000/balance',
        json={
            'api_key': API_KEY,
            'number_invoice': str(invoice)
        }
    )

    decoded_balance = json.loads(balance.content)['balance']

    return decimal.Decimal(decoded_balance)


def compare_balance_with_payment_amount(invoice, payment_amount):
    """
    Сравнивает текущий баланс пользователя с суммой, которую он хочет
    заплатить.
    """
    buyer_balance = get_user_balance(
        invoice=invoice
    )

    if buyer_balance > payment_amount:
        return True
    return False


