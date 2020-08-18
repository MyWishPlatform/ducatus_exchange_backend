from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ducatus_exchange.quantum.models import Charge
from ducatus_exchange.quantum.api import initiate_charge


class ChargeSerializer(serializers.ModelSerializer):
    currencies = ['USD', 'EUR', 'GBP', 'CHF']

    class Meta:
        model = Charge
        fields = '__all__'

    def create(self, validated_data):
        charge_info = initiate_charge(validated_data)

        validated_data = {
            'charge_id': charge_info['id'],
            'status': charge_info['status'],
            'currency': charge_info['chargeAmount']['currencyCode'],
            'amount': charge_info['chargeAmount']['value'],
            'hash': charge_info['hash'],
            'redirect_url': charge_info['url'],
            'email': validated_data['email']
        }

        return super().create(validated_data)

    def is_valid(self, raise_exception=False):
        if self.data['currency'] not in self.currencies:
            if raise_exception:
                raise ValidationError(detail=f'currency must be in {self.currencies}')
            return False

        if self.data['amount'] < 1:
            if raise_exception:
                raise ValidationError(detail=f'amount must be greater or equal then 1')
            return False

        return True
