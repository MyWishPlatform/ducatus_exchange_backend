import pika
import os
import traceback
import threading
import json
import sys
from types import FunctionType


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_widget.settings')
import django
django.setup()

from ducatus_widget.settings import BACKEND_WALLETS
from ducatus_widget.payments.api import parse_payment_message


class Receiver(threading.Thread):

    def __init__(self, queue):
        super().__init__()
        self.network = queue

    def run(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            'localhost',
            5672,
            'ducatus_widget',
            pika.PlainCredentials('ducatus_widget', 'ducatus_widget'),
        ))

        channel = connection.channel()

        queue_name = BACKEND_WALLETS[self.network]['queue']
        print(queue_name)

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

        print('receiver start ', self.network, flush=True)
        channel.start_consuming()

    def payment(self, message):
        print('payment message', flush=True)
        print('message["amount"]', message['amount'])
        print('payment ok', flush=True)
        parse_payment_message(message)

    def callback(self, ch, method, properties, body):
        print('received', body, properties, method, flush=True)
        try:
            message = json.loads(body.decode())
            if message.get('status', '') == 'COMMITTED':
                getattr(self, properties.type, self.unknown_handler)(message)
        except Exception as e:
            print('\n'.join(traceback.format_exception(*sys.exc_info())),
                  flush=True)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def unknown_handler(self, message):
        print('unknown message', message, flush=True)


networks = BACKEND_WALLETS.keys()


for network in networks:
    rec = Receiver(network)
    rec.start()



