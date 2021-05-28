from rest_framework import serializers

from ducatus_exchange.stats.models import StatisticsAddress


class DucxWalletsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatisticsAddress
        fields = ('user_address', 'balance')
