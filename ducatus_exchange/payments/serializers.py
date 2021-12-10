from rest_framework import serializers

from ducatus_exchange.payments.models import Payment


class PaymentStatusSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    converted_from = serializers.SerializerMethodField()
    converted_from_amount = serializers.SerializerMethodField()
    converted_to = serializers.SerializerMethodField()
    converted_to_amount = serializers.SerializerMethodField()
    sent_from = serializers.SerializerMethodField()
    sent_to = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = (
            'status',
            'converted_from',
            'converted_from_amount',
            'converted_to',
            'converted_to_amount',
            'sent_from',
            'sent_to',
            'transfer_state_history')

    def get_status(self, obj):
        return obj.adapted_state

    def get_converted_from(self, obj):
        return obj.currency

    def get_converted_from_amount(self, obj):
        return obj.original_amount

    def get_converted_to(self, obj):
        return obj.exchange_request.user.platform

    def get_converted_to_amount(self, obj):
        return obj.sent_amount

    def get_sent_from(self, obj):
        exr = obj.exchange_request
        keys = ('DUC', 'DUCX', 'BTC', 'ETH')
        values = (exr.duc_address, exr.ducx_address,
                  exr.btc_address, exr.eth_address)
        return dict(zip(keys, values))[obj.currency]

    def get_sent_to(self, obj):
        return obj.exchange_request.user.address


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
