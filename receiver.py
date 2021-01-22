import pika
import os
import traceback
import threading
import json
import sys
from types import FunctionType


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')
import django
django.setup()

from django.core.exceptions import ObjectDoesNotExist
from ducatus_exchange.settings import NETWORK_SETTINGS
from ducatus_exchange.payments.api import parse_payment_message, TransferException
from ducatus_exchange.transfers.api import confirm_transfer


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

        print(
            'RECEIVER MAIN: started on {net} with queue `{queue_name}`'
            .format(net=self.network, queue_name=queue_name), flush=True
        )

        channel.start_consuming()

    def payment(self, message):
        print('PAYMENT MESSAGE RECEIVED', flush=True)
        parse_payment_message(message)

    def transferred(self, message):
        print('TRANSFER CONFIRMATION RECEIVED', flush=True)
        confirm_transfer(message)

    def callback(self, ch, method, properties, body):
        print('received', body, properties, method, flush=True)
        try:
            message = json.loads(body.decode())
            if message.get('status', '') == 'COMMITTED':
                getattr(self, properties.type, self.unknown_handler)(message)
        except ObjectDoesNotExist as e:
            print('Could not find onject in database', flush=True)
            print(e, flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except TransferException:
            print('Exception in transfer, saving payment and cancelling transfer', flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print('\n'.join(traceback.format_exception(*sys.exc_info())),
                  flush=True)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def unknown_handler(self, message):
        print('unknown message', message, flush=True)


networks = NETWORK_SETTINGS.keys()


for network in networks:
    rec = Receiver(network)
    rec.start()



