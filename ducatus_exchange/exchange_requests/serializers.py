from rest_framework import serializers

from .models import ExchangeStatus


class ExchangeStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExchangeStatus
        fields = (
            'status',
            'updated_at',
            'duc_balance',
            'ducx_balance'
        )
