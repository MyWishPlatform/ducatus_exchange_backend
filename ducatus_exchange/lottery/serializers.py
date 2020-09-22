from rest_framework import serializers

from ducatus_exchange.lottery.models import Lottery, LotteryPlayer
from ducatus_exchange.consts import DECIMALS, BONUSES_FOR_TICKETS


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

    def to_representation(self, instance, with_description=True):
        res = super().to_representation(instance)
        res['sent_duc_amount'] = int(res['sent_duc_amount']) // DECIMALS['DUC']
        res['duc_amount'] = int(res['duc_amount']) // DECIMALS['DUC']

        if instance.winner_numbers and instance.winner_players_ids:
            res['winner_numbers'] = instance.winner_numbers
            res['winners_data'] = []
            for winner_id in instance.winner_players_ids:
                winner_player = LotteryPlayer.objects.get(id=winner_id)
                res['winners_data'].append({
                    'address': winner_player.user.address,
                    'tx_hash': winner_player.transfer.tx_hash,
                })

        if not with_description:
            res.pop('description')
            res.pop('image')
            res.pop('video')

        return res


class LotteryPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LotteryPlayer
        fields = ['id', 'lottery', 'sent_usd_amount', 'tickets_amount', 'received_duc_amount']

    def to_representation(self, instance, is_admin=False):
        res = super().to_representation(instance)
        res['address'] = instance.user.address
        res['tx_hash'] = instance.transfer.tx_hash if instance.transfer.tx_hash else None
        res['received_duc_amount'] = int(res['received_duc_amount']) // DECIMALS['DUC']
        if is_admin:
            res['back_office_code'] = instance.back_office_code
            res['e_commerce_code'] = instance.e_commerce_code
            res['back_office_percent'] = BONUSES_FOR_TICKETS[instance.tickets_amount]['back_office_bonus']
            res['e_commerce_percent'] = BONUSES_FOR_TICKETS[instance.tickets_amount]['e_commerce_bonus']
        return res
