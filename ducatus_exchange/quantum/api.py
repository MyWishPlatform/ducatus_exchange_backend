import json
import requests
import datetime
from django.utils import timezone

from ducatus_exchange.quantum.models import QuantumAccount
from ducatus_exchange.settings import QUANTUM_CLIENT_ID, QUANTUM_CLIENT_SECRET


class QuantumApiError(Exception):
    pass


def initiate_charge(validated_data):
    quantum_account = QuantumAccount.objects.first()
    update_access_token(quantum_account)

    new_charge_data = {
        'amount': {
            'currencyCode': validated_data['currency'],
            'value': validated_data['amount'],
        },
        'email': validated_data['email'],
        'tokenCurrencyCode': f'Q{validated_data["currency"]}',
        'receivingAccountAddress': quantum_account.address,
        'returnUrl': 'https://ducsite.rocknblock.io/buy',
    }

    headers = {
        'Authorization': '{token_type} {access_token}'.format(token_type=quantum_account.token_type,
                                                              access_token=quantum_account.access_token)
    }

    try:
        creation_request = requests.post('https://sandbox.quantumclearance.com/api/v1/merchant/charges',
                                         json=new_charge_data,
                                         headers=headers)
    except Exception:
        raise QuantumApiError

    return json.loads(creation_request.content)


def update_access_token(quantum_account: QuantumAccount):
    token_expiration_delta = quantum_account.token_expires_at + datetime.timedelta(minutes=5).seconds
    if not quantum_account.access_token or token_expiration_delta < timezone.now().timestamp():
        request_data = {
            'client_id': QUANTUM_CLIENT_ID,
            'client_secret': QUANTUM_CLIENT_SECRET,
            'grant_type': 'client_credentials',
        }
        new_token_request = requests.post('https://sandbox.quantumclearance.com/connect/token', data=request_data)
        token_info = json.loads(new_token_request.content)

        quantum_account.token_type = token_info['token_type']
        quantum_account.access_token = token_info['access_token']
        quantum_account.token_expires_at = timezone.now().timestamp() + token_info['expires_in']
        quantum_account.save()