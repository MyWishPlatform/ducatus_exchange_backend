import logging

from django.db.transaction import atomic
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ducatus_exchange.exchange_requests.models import ExchangeRequest
from ducatus_exchange.payments.api import register_payment
from ducatus_exchange.payments.models import Payment


logger = logging.getLogger(__name__)


ADDRESSES_TYPES = {
    "Ducatus": {"address": "duc_address", "currency": "DUC"},
    "Ducatusx": {"address": "ducx_address", "currency": "DUCX"},
    "Bitcoin": {"address": "btc_address", "currency": "BTC"},
    "Etherium": {"address": "eth_address", "currency": "ETH"}
}


class AddressesToScan(APIView):

    @classmethod
    def get(cls, request) -> Response:

        try:
            network = request.query_params['network']
            address = ADDRESSES_TYPES[network]["address"]
            queryset = ExchangeRequest.objects.all().only(address)
        except KeyError:
            logger.debug('Bad request')
            return Response(status=status.HTTP_400_BAD_REQUEST)

        addresses = [i.__getattribute__(address) for i in queryset]
        logger.debug('Addresses successfully repast')
        return Response({"addresses": addresses}, status=status.HTTP_200_OK)


class PaymentHandler(APIView):

    @classmethod
    def post(cls, request) -> Response:
        with atomic():
            request_data = request.data

            tx_hash = request_data.get("transaction_hash")
            if Payment.objects.filter(tx_hash=tx_hash).count():
                return Response(status=status.HTTP_208_ALREADY_REPORTED)

            network = request_data.get("network")
            address_to = request_data.get("address_to")

            filter_data = {
                f'{ADDRESSES_TYPES.get(network).get("address")}__iexact': address_to
            }

            exchange = ExchangeRequest.objects.get(**filter_data)
            if not exchange:
                return Response(status=status.HTTP_204_NO_CONTENT)

            exchange_id = exchange.id
            amount = request_data.get("amount")
            currency = ADDRESSES_TYPES[network]["currency"]
            address_from = request_data.get("address_from")
            register_payment(exchange_id, tx_hash, currency, amount, address_from)

            logger.info('LOG RECEIVED')

            return Response(status=status.HTTP_201_CREATED)
