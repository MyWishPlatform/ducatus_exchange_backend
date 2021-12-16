from rest_framework import serializers

from ducatus_exchange.payments.models import Payment


class PaymentStatusSerializer(serializers.ModelSerializer):
    txid = serializers.CharField(source='tx_hash')
    status = serializers.CharField(source='adapted_state')
    convertedFrom = serializers.CharField(source='currency')
    convertedFromAmount = serializers.CharField(source='original_amount')
    convertedTo = serializers.CharField(source='exchange_request.user.platform')
    convertedToAmount = serializers.CharField(source='sent_amount')
    sentTo = serializers.CharField(source='exchange_request.user.address')
    statusHistory = serializers.JSONField(source='transfer_state_history')

    class Meta:
        model = Payment
        fields = (
            'txid',
            'status',
            'convertedFrom',
            'convertedFromAmount',
            'convertedTo',
            'convertedToAmount',
            'sentTo',
            'statusHistory')


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
