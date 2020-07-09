from rest_framework import serializers

from ducatus_exchange.lottery.models import Lottery, LotteryPlayer


class LotterySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lottery
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'received_usd_amount': {'read_only': True}
        }


class LotteryPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LotteryPlayer
        fields = ['lottery', 'sent_usd_amount', 'tickets_amount']

    def to_representation(self, instance):
        res = super().to_representation(instance)
        res['address'] = instance.user.address
        return res
