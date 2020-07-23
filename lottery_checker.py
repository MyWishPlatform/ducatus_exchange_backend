import os
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')
import django

django.setup()

from django.utils import timezone
from ducatus_exchange.lottery.models import Lottery, DucatusUser
from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.settings import LOTTERY_CLOSING_INTERVAL, LOTTERY_CHECKER_INTERVAL
from ducatus_exchange.consts import DECIMALS

if __name__ == '__main__':
    while True:
        for lottery in Lottery.objects.filter(ended=False):
            if lottery.sent_duc_amount // DECIMALS['DUC'] >= lottery.duc_amount // DECIMALS[
                'DUC'] and lottery.filled_at:
                if timezone.now().timestamp() - lottery.filled_at > LOTTERY_CLOSING_INTERVAL:
                    lottery.ended = True
                    # temporarily hardcode
                    lottery.winner_transfer = DucatusTransfer.objects.first()
                    lottery.winner_user = lottery.winner_transfer.payment.exchange_request.user
                    lottery.save()
                    print('lottery {} with id {} closed'.format(lottery.name, lottery.id), flush=True)

        time.sleep(LOTTERY_CHECKER_INTERVAL)