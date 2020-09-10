from rest_framework import serializers

from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.payments.models import Payment

from ducatus_exchange.exchange_requests.models import ExchangeRequest


class DucatusTransferSerializer(serializers.ModelSerializer):
    exchange_request = serializers.PrimaryKeyRelatedField(queryset=ExchangeRequest.objects)
    payment = serializers.PrimaryKeyRelatedField(queryset=Payment.objects)

    class Meta:
        model = DucatusTransfer
        fields = ('exchange_request', 'tx_hash', 'amount', 'payment',
                  'currency', 'state')
