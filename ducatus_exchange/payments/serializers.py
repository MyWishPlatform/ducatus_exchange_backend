from rest_framework import serializers

from ducatus_exchange.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = (
            'tx_hash',
            'currency',
            'original_amount',
            'rate',
            'sent_amount',
            'created_date',
            'transfer_state',
            'collection_state',
            'collection_tx_hash',
            'returned_tx_hash',
        )
        lookup_field = 'tx_hash'
