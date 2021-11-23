import os
from ducatus_exchange.bot.base import Bot


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')
import django
django.setup()


if __name__ == '__main__':
    Bot().start()

