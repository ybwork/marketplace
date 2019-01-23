import decimal
import json
import requests

from mysite.settings import API_KEY


def get_user_balance(number_invoice):
    balance = requests.get(
        'http://127.0.0.1:5000/balance',
        json={
            'api_key': API_KEY,
            'number_invoice': str(number_invoice)
        }
    )

    decoded_balance = json.loads(balance.content)['balance']

    return decimal.Decimal(decoded_balance)

