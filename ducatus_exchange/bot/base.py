import logging
import os
import sys
import threading
import time
import traceback
import telebot

from django.db import IntegrityError
from ducatus_exchange.bot.models import BotSub
from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
from ducatus_exchange.parity_interface import ParityInterface
# from ducatus_exchange.settings import BOT_TOKEN, NETWORK_SETTINGS
from ducatus_exchange.settings import NETWORK_SETTINGS, BOT_TOKEN

logger = logging.getLogger('bot')


class Bot(threading.Thread):
    def __init__(self):
        super().__init__()
        self.bot = telebot.TeleBot(BOT_TOKEN)

        @self.bot.message_handler(commands=['start'])
        def start_handler(message):
            try:
                BotSub(chat_id=message.chat.id).save()
                self.bot.reply_to(message, 'Hello!')
            except IntegrityError:
                pass

        @self.bot.message_handler(commands=['stop'])
        def stop_handler(message):
            try:
                BotSub.objects.get(chat_id=message.chat.id).delete()
                self.bot.reply_to(message, 'Bye!')
            except BotSub.DoesNotExist:
                pass


        @self.bot.message_handler(commands=['balance'])
        def balance_handle(message):
            try:
                ducx_balance = ParityInterface().get_balance()
                duc_balance = DucatuscoreInterface().get_balance()
                self.bot.reply_to(
                    message, 
                    f'DUC balance: {duc_balance}\nDUCX balance {ducx_balance / (10 ** 18)}')
            except Exception as e:
                logger.info(msg=f'Error while handling message_handler balance with exception:\n {e}')


        @self.bot.message_handler(commands=['address'])
        def address_handle(message):
            try:
                ducx_address = NETWORK_SETTINGS['DUCX']['address']
                duc_address = DucatuscoreInterface().rpc.getaccountaddress('')
                self.bot.reply_to(message, f'DUC balance: {duc_address}\nDUCX balance {ducx_address}')
            except Exception as e:
                logger.info(msg=f'Error while handling message_handler address with exception:\n {e}')


        @self.bot.message_handler(commands=['ping'])
        def ping_handler(message):
            self.bot.reply_to(message, 'Pong')

    def run(self):
        while True:
            try:
                self.bot.polling(none_stop=True)
            except Exception:
                print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)
                time.sleep(15)

bot = Bot()
