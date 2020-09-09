from rest_framework import serializers

from ducatus_exchange.transfers.models import DucatusTransfer


class DucatusTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = DucatusTransfer
        fields = ('exchange_request', 'tx_hash', 'amount', 'currency', 'state')
