from rest_framework import serializers

from ducatus_exchange.lottery.models import Lottery, LotteryPlayer
from ducatus_exchange.consts import DECIMALS


class LotterySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lottery
        fields = (
            'id', 'name', 'description', 'image', 'duc_amount', 'sent_duc_amount', 'started_at', 'ended', 'filled_at',
            'gave_tickets_amount', 'video')
        extra_kwargs = {
            'id': {'read_only': True},
            'sent_duc_amount': {'read_only': True}
        }

    def to_representation(self, instance):
        res = super().to_representation(instance)
        res['sent_duc_amount'] = int(res['sent_duc_amount']) // DECIMALS['DUC']
        res['duc_amount'] = int(res['duc_amount']) // DECIMALS['DUC']
        res['winner_address'] = instance.winner_user.address if instance.winner_user else None
        res['winner_tx_hash'] = instance.winner_transfer.tx_hash if instance.winner_transfer else None

        return res


class LotteryPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LotteryPlayer
        fields = ['lottery', 'sent_usd_amount', 'tickets_amount', 'received_duc_amount']

    def to_representation(self, instance):
        res = super().to_representation(instance)
        res['address'] = instance.user.address
        res['tx_hash'] = instance.transfer.tx_hash if instance.transfer.tx_hash else None
        res['received_duc_amount'] = int(res['received_duc_amount']) // DECIMALS['DUC']
        return res
