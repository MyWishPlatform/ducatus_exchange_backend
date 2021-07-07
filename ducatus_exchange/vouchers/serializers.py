import datetime
from django.utils import timezone

from rest_framework import serializers

from ducatus_exchange.vouchers.models import Voucher, FreezingVoucher, VoucherInput
from ducatus_exchange.freezing.serializers import CltvDetailsSerializer
from ducatus_exchange.freezing.api import get_duc_transfer_fee
from ducatus_exchange.consts import DECIMALS


class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = ('id', 'voucher_code', 'activation_code', 'usd_amount', 'is_active', 'is_used', 'publish_date',
                  'activation_date', 'lock_days', 'charge_id', 'payment_id')
        extra_kwargs = {
            'id': {'read_only': True},
            'activation_code': {'read_only': True},
            'is_used': {'read_only': True},
            'publish_date': {'read_only': True},
            'activation_date': {'read_only': True}
        }


class VoucherInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoucherInput
        fields = '__all__'


class FreezingVoucherSerializer(serializers.ModelSerializer):
    cltv_details = CltvDetailsSerializer(read_only=True)
    voucherinput_set = VoucherInputSerializer(many=True, read_only=True)

    class Meta:
        model = FreezingVoucher
        fields = ('id', 'wallet_id', 'user_duc_address', 'cltv_details', 'voucherinput_set')

    def to_representation(self, instance):
        res = super().to_representation(instance)

        res['tx_fee'] = get_duc_transfer_fee()
        res['ready_to_withdraw'] = instance.cltv_details.lock_time + datetime.timedelta(
            minutes=10).seconds < timezone.now().timestamp()

        transfer_instance = instance.voucher.transfer_set.first()
        res['duc_amount'] = int(transfer_instance.duc_amount) // DECIMALS['DUC']
        res['usd_amount'] = instance.voucher.usd_amount

        return res
