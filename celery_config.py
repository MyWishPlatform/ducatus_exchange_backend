import celery
from celery.schedules import crontab
import os
import logging
from dateutil import tz
eastern = tz.gettz('Europe/Moscow')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')
import django
django.setup()

from ducatus_exchange.exchange_requests.utils import dayly_reset, weekly_reset
from ducatus_exchange.stats.mongo_checker import get_duc_balances
from ducatus_exchange.stats.api import update_nodes
from ducatus_exchange.settings import RABBITMQ_URL

logger = logging.getLogger('task')

app = celery.Celery(
    'task', 
    broker=RABBITMQ_URL,
    include=[
        'ducatus_exchange.payments.tasks',
        'ducatus_exchange.exchange_requests.tasks',
        'ducatus_exchange.transfers.tasks',
    ]
)


@app.task
def reset_dayly():
    logger.info(msg='Starting dayly reset')
    dayly_reset()
    logger.info(msg='dayly reset complete')


@app.task
def reset_weekly():
    logger.info(msg='Starting weekly reset')
    weekly_reset()
    logger.info(msg='weekly reset complete')


@app.task
def update_duc_balances():
    logger.info(msg='Starting DUC balance updating')
    get_duc_balances()
    logger.info(msg='DUC balance updating complete')


@app.task
def update_ducx_node_balandes():
    logger.info(msg='Starting DUCX node balance updating')
    update_nodes()
    logger.info(msg='DUC node balance updating complete')


app.conf.beat_schedule = {
    'dayly_task': {
        'task': 'task.reset_dayly',
        'schedule': crontab(hour=0, minute=0),
    },
    'weekly_task': {
        'task': 'task.reset_weekly',
        'schedule': crontab(day_of_week=0, hour=0, minute=0),
    },
    'update_duc': {
        'task': 'task.update_duc_balances',
        'schedule': crontab(hour=12, minute=0),
    },
    'update_ducx_nodes': {
        'task': 'task.update_ducx_node_balances',
        'schedule': crontab(minute=0),
    },
    'process_queued_duc_transfer': {
        'task': 'ducatus_exchange.payments.tasks.process_queued_duc_transfer',
        'schedule': crontab(minute='*'),
    },
    'update_duc_and_ducx_balances': {
        'task': 'ducatus_exchange.exchange_requests.tasks.update_duc_and_ducx_balances',
        'schedule': crontab(minute='*'),
    },
    'confirm_transfers': {
        'task': 'ducatus_exchange.transfers.tasks.confirm_transfers',
        'schedule': crontab(minute='*'),
    },
    'parse_logs': {
        'task': 'ducatus_exchange.payments.tasks.process_payments',
        'schedule': crontab(minute='*'),
    },
}
