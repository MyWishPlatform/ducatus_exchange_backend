import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')
import django
django.setup()

from ducatus_exchange.bot.base import Bot


if __name__ == '__main__':
    Bot().start()
