from rest_framework import serializers

from ducatus_exchange.vtransfers.models import Transfer
from ducatus_exchange.consts import DECIMALS


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = ['duc_address', 'duc_amount', 'tx_hash', 'transfer_status']
        extra_kwargs = {
            'tx_hash': {'read_only': True},
            'transfer_status': {'read_only': True},
        }

    def to_representation(self, instance):
        res = super().to_representation(instance)
        res['usd_amount'] = instance.voucher.usd_amount
        res['duc_amount'] = int(res['duc_amount']) // DECIMALS['DUC']
        res['lock_days'] = instance.voucher.lock_days
        return res
