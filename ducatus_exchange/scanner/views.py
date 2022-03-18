from django.db.transaction import atomic
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ducatus_exchange.exchange_requests.models import ExchangeRequest
from ducatus_exchange.payments.api import parse_payment_message


ADDRESSES_TYPES = {
        "Ducatus": {"address": "duc_address", "currency": "DUC"},
        "Ducatusx": {"address": "ducx_address", "currency": "DUCX"},
        "Bitcoin": {"address": "btc_address", "currency": "BTC"},
        "Etherium": {"address": "eth_address", "currency": "ETH"}
    }


class AddressesToScan(APIView):

    @classmethod
    def get(cls, request, network: str) -> Response:

        try:
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
            message = {
                'exchangeId': exchange_id,
                'fromAddress': address_from,
                'address': address_to,
                'transactionHash': tx_hash,
                'currency': currency,
                'amount': amount,
            }
            try:
                parse_payment_message(message=message)
                return Response(message, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
