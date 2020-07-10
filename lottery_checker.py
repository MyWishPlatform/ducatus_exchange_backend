import os
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')
import django

django.setup()

from django.utils import timezone
from ducatus_exchange.lottery.models import Lottery
from ducatus_exchange.settings import LOTTERY_CLOSING_INTERVAL, LOTTERY_CHECKER_INTERVAL

if __name__ == '__main__':
    while True:
        for lottery in Lottery.objects.all():
            if lottery.sent_duc_amount >= lottery.duc_amount and lottery.filled_at:
                if timezone.now().timestamp() - lottery.filled_at > LOTTERY_CLOSING_INTERVAL:
                    lottery.ended = True
                    lottery.save()
                    print('lottery {} with id {} closed'.format(lottery.name, lottery.id), flush=True)

        time.sleep(LOTTERY_CHECKER_INTERVAL)
