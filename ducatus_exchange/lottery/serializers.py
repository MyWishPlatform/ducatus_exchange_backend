from rest_framework import serializers

from ducatus_exchange.lottery.models import Lottery


class LotterySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lottery
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'received_usd_amount': {'read_only': True}
        }
