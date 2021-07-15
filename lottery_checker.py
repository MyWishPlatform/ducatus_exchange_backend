import os
import time
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')
import django

django.setup()

from django.utils import timezone
from ducatus_exchange.lottery.models import Lottery, LotteryPlayer
from ducatus_exchange.settings import LOTTERY_CLOSING_INTERVAL, LOTTERY_CHECKER_INTERVAL
from random_contract.executor import finalize_lottery

logger = logging.getLogger('lottery_checker')

if __name__ == '__main__':

    while True:
        for lottery in Lottery.objects.filter(ended=False):
            if lottery.sent_duc_amount >= lottery.duc_amount and lottery.filled_at:
                if timezone.now().timestamp() - lottery.filled_at > LOTTERY_CLOSING_INTERVAL:
                    winners = finalize_lottery(lottery.gave_tickets_amount)

                    lottery.winner_numbers = winners
                    winner_users = [None] * len(winners)

                    tickets_amount = 0
                    for lottery_player in LotteryPlayer.objects.order_by('id'):
                        if not all(winner_users):
                            prev_tickets_amount = tickets_amount
                            tickets_amount += lottery_player.tickets_amount
                            for i, winner_number in enumerate(winners):
                                if prev_tickets_amount < winner_number <= tickets_amount:
                                    winner_users[i] = lottery_player.id
                        else:
                            break

                    lottery.winner_players_ids = winner_users

                    lottery.ended = True
                    lottery.save()

                    lottery.send_mails_to_winners()
                    logger.info(msg=f'lottery {lottery.name} with id {lottery.id} closed')

        time.sleep(LOTTERY_CHECKER_INTERVAL)
