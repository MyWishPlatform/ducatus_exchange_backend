import logging
import os
import sys
import threading
import time
import traceback
import telebot

from django.db import IntegrityError
from ducatus_exchange.bot.models import BotSub
from ducatus_exchange.bitcoin_api import DucatuscoreInterface
from ducatus_exchange.parity_interface import ParityInterface
from ducatus_exchange.consts import DECIMALS
from ducatus_exchange.settings import NETWORK_SETTINGS, BOT_TOKEN

logger = logging.getLogger('bot')


class Bot(threading.Thread):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Bot, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        super().__init__()
        self.bot = telebot.TeleBot(BOT_TOKEN)

        @self.bot.message_handler(commands=['start'])
        def start_handler(message):
            logger.info('run start handler')
            try:
                BotSub(chat_id=message.chat.id).save()
                self.bot.reply_to(message, 'Hello!')
            except IntegrityError:
                pass

        @self.bot.message_handler(commands=['stop'])
        def stop_handler(message):
            logger.info('run stop handler')
            try:
                BotSub.objects.get(chat_id=message.chat.id).delete()
                self.bot.reply_to(message, 'Bye!')
            except BotSub.DoesNotExist:
                pass


        @self.bot.message_handler(commands=['balances'])
        def balances_handle(message):
            logger.info('run balances handler')
            ducx_balance = ParityInterface().get_balance()
            duc_rpc = DucatuscoreInterface(NETWORK_SETTINGS["DUC"], DECIMALS["DUC"])
            duc_balance = duc_rpc.get_balance()
            response = f'DUC balance: {duc_balance / DECIMALS["DUC"]}\nDUCX balance {ducx_balance / DECIMALS["DUCX"]}'
            self.bot.reply_to(message, response)


        @self.bot.message_handler(commands=['addresses'])
        def addresses_handle(message):
            logger.info('run addresses handler')
            ducx_address = NETWORK_SETTINGS['DUCX']['address']
            duc_rpc = DucatuscoreInterface(NETWORK_SETTINGS["DUC"], DECIMALS["DUC"])
            duc_address = duc_rpc.get_account_address()
            response = f'DUC balance: {duc_address}\nDUCX balance {ducx_address}'
            self.bot.reply_to(message, response)


        @self.bot.message_handler(commands=['ping'])
        def ping_handler(message):
            logger.info('run ping handler')
            self.bot.reply_to(message, 'Pong')

    def run(self):
        while True:
            try:
                self.bot.polling(none_stop=True)
            except Exception:
                print('\n'.join(traceback.format_exception(*sys.exc_info())), flush=True)
                time.sleep(15)
