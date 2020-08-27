from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ducatus_exchange.consts import DECIMALS
from ducatus_exchange.quantum.models import Charge
from ducatus_exchange.quantum.api import initiate_charge


class ChargeSerializer(serializers.ModelSerializer):
    currencies = ['USD', 'EUR', 'GBP', 'CHF']

    class Meta:
        model = Charge
        fields = ['amount', 'currency', 'duc_address', 'email']

    def create(self, validated_data):
        charge_info = initiate_charge(validated_data)

        currency = charge_info['chargeAmount']['currencyCode']
        validated_data = {
            'charge_id': charge_info['id'],
            'status': charge_info['status'],
            'currency': currency,
            'amount': charge_info['chargeAmount']['value'] * DECIMALS[currency],
            'hash': charge_info['hash'],
            'redirect_url': charge_info['url'],
            'email': validated_data['email'],
            'duc_address': validated_data['duc_address'],
            'exchange_request': validated_data['exchange_request']
        }

        return super().create(validated_data)

    def validate_currency(self, value):
        if value not in self.currencies:
            raise ValidationError(detail=f'currency must be in {self.currencies}')
        return value

    def validate_amount(self, value):
        if value < 0:
            raise ValidationError(detail=f'amount must be greater or equal then 1')
        return value
