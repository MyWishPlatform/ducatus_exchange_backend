from rest_framework import serializers

from ducatus_exchange.transfers.models import DucatusTransfer


class DucatusTransferSerializer(serializers.ModelSerializer):
    exchange_request = serializers.PrimaryKeyRelatedField(read_only=True)
    payment = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = DucatusTransfer
        fields = ('exchange_request', 'tx_hash', 'amount', 'payment',
                  'currency', 'state')
