from rest_framework import serializers

from ducatus_exchange.lottery.models import Lottery, LotteryPlayer
from ducatus_exchange.consts import DECIMALS


class LotterySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lottery
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'received_usd_amount': {'read_only': True}
        }

    def to_representation(self, instance):
        res = super().to_representation(instance)
        res['sent_duc_amount'] = int(res['sent_duc_amount']) // DECIMALS['DUC']
        res['duc_amount'] = int(res['duc_amount']) // DECIMALS['DUC']
        return res


class LotteryPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LotteryPlayer
        fields = ['lottery', 'sent_usd_amount', 'tickets_amount']

    def to_representation(self, instance):
        res = super().to_representation(instance)
        res['address'] = instance.user.address
        return res
