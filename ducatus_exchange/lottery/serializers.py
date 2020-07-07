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
        fields = '__all__'
        read_only_fields = '__all__'
