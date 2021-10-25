import pika
import os
import traceback
import threading
import json
import sys
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')
import django
django.setup()

from django.core.exceptions import ObjectDoesNotExist
from ducatus_exchange.settings import NETWORK_SETTINGS

logger = logging.getLogger('receiver')


class Receiver(threading.Thread):

    def __init__(self, queue):
        super().__init__()
        self.network = queue

    def run(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            'localhost',
            5672,
            'ducatus_exchange',
            pika.PlainCredentials('ducatus_exchange', 'ducatus_exchange'),
            heartbeat=3600,
            blocked_connection_timeout=3600
        ))

        channel = connection.channel()

        queue_name = NETWORK_SETTINGS[self.network]['queue']

        channel.queue_declare(
                queue=queue_name,
                durable=True,
                auto_delete=False,
                exclusive=False
        )
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=self.callback
        )

        logger.info(msg=f'RECEIVER MAIN: started on {self.network} with queue `{queue_name}`')

        channel.start_consuming()

    def payment(self, message):
        # import function locally avoiding circle imports
        from ducatus_exchange.payments.api import parse_payment_message

        logger.info(msg='PAYMENT MESSAGE RECEIVED')
        parse_payment_message(message)

    def transferred(self, message):
        # import function locally avoiding circle imports
        from ducatus_exchange.transfers.api import confirm_transfer
        
        logger.info(msg='TRANSFER CONFIRMATION RECEIVED')
        confirm_transfer(message)

    def callback(self, ch, method, properties, body):
        # import function locally avoiding circle imports
        from ducatus_exchange.payments.api import TransferException

        logger.info(msg=f'received {body} {properties} {method}')
        try:
            message = json.loads(body.decode())
            if message.get('status', '') == 'COMMITTED':
                getattr(self, properties.type, self.unknown_handler)(message)
        except ObjectDoesNotExist as e:
            logger.error(msg='Could not find onject in database')
            logger.error(msg=e)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except TransferException:
            logger.info(msg='Exception in transfer, saving payment and cancelling transfer')
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(msg=('\n'.join(traceback.format_exception(*sys.exc_info()))))
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def unknown_handler(self, message):
        logger.info(msg=f'unknown message {message}')


networks = NETWORK_SETTINGS.keys()


for network in networks:
    rec = Receiver(network)
    rec.start()
