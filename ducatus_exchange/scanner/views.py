import json
from dataclasses import dataclass
from typing import Union

from django.db.transaction import atomic
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ducatus_exchange.exchange_requests.models import ExchangeRequest
from ducatus_exchange.payments.api import parse_payment_message
from ducatus_exchange.settings import NETWORK_SETTINGS


ADDRESSES_TYPES = {
        "Ducatus": {"address": "duc_address", "currency": "DUC"},
        "Ducatusx": {"address": "ducx_address", "currency": "DUCX"},
        "Bitcoin": {"address": "btc_address", "currency": "BTC"},
        "Etherium": {"address": "eth_address", "currency": "ETH"}
    }


TRANSFER_ABI = {
                'anonymous': False,
                'inputs': [{'indexed': True, 'name': 'from', 'type': 'address'},
                           {'indexed': True, 'name': 'to', 'type': 'address'},
                           {'indexed': False, 'name': 'value', 'type': 'uint256'}],
                'name': 'Transfer',
                'type': 'event'
}


class AddressesToScan(APIView):

    @classmethod
    def get(cls, request) -> Response:
        try:
            network = request.query_params['network']
            queryset = ExchangeRequest.objects.filter(payment=None).only(ADDRESSES_TYPES[network]["address"])
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        addresses = [i.__getattribute__(ADDRESSES_TYPES[network]["address"]) for i in queryset]

        return Response({"addresses": addresses}, status=status.HTTP_200_OK)


class PaymentHandler(APIView):

    @classmethod
    def post(cls, request) -> Response:
        
        with atomic():
            request_data = request.data
            network = request_data.get("network")
            address_to = request_data.get("address_to")
            filter_data = {
                ADDRESSES_TYPES.get(network).get("address"): address_to
            }
            exchange_id = ExchangeRequest.objects.get(**filter_data).id
            amount = request_data.get("amount")
            currency = ADDRESSES_TYPES[network]["currency"]
            tx_hash = request_data.get("transaction_hash")
            address_from = request_data.get("address_from")
            message = Message(
                exchangeId=exchange_id,
                amount=amount,
                currency=currency,
                transactionHash=tx_hash,
                fromAddress=address_from,
                address=address_to
                )

            return parse_message(message)


class EventsForScann(APIView):

    @classmethod
    def get(cls, request):

        request_message = [{"network": "Etherium", "contracts": list()}]

        for token_name, token_data in NETWORK_SETTINGS['ETH']['tokens'].items():
            request_message[0]["contracts"].append({
                "address": token_data.get("address"),
                "abi": TRANSFER_ABI
            })
        return Response(request_message, status=status.HTTP_200_OK)


class ERC20PaymentHandler(APIView):

    @classmethod
    def post(cls, request) -> Response:

        with atomic():
            request_data = request.data
            network = request_data.get("network")
            tx_hash = request_data.get('tx_hash')
            data = json.loads(request_data.get("data"))
            address_to = data.get('to')
            filter_data = {
                ADDRESSES_TYPES.get(network).get("address"): address_to
            }
            exchange_id = ExchangeRequest.objects.get(**filter_data).id
            currency = ADDRESSES_TYPES[network]["currency"]
            amount = data.get('value')
            from_address = data.get('from')
            message = Message(
                exchangeId=exchange_id,
                currency=currency,
                amount=amount,
                fromAddress=from_address,
                address=address_to,
                transactionHash=tx_hash
            )

            return parse_message(message)


@dataclass
class Message:
    exchangeId: int
    fromAddress: str
    address: str
    transactionHash: str
    currency: str
    amount: int

    def __getitem__(self, item) -> Union[int, str]:
        return getattr(self, item)


def parse_message(message: Message) -> Response:
    try:
        parse_payment_message(message=message.__dict__)
        return Response(message, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(e, status=status.HTTP_400_BAD_REQUEST)
