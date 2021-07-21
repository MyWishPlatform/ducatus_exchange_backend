from rest_framework import serializers

from ducatus_exchange.stats.models import StatisticsAddress, BitcoreAddress


class DucWalletsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatisticsAddress
        fields = ('user_address', 'balance')


class BitcoreWalletsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BitcoreAddress
        fields = ('user_address', 'balance')
