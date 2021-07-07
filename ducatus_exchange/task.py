import celery
from celery.schedules import crontab
import datetime
import os
from dateutil import tz
eastern = tz.gettz('Europe/Moscow')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ducatus_exchange.settings')
import django
django.setup()

from ducatus_exchange.exchange_requests.utils import dayly_reset, weekly_reset
from ducatus_exchange.stats.mongo_checker import get_duc_balances
from ducatus_exchange.stats.api import update_nodes

app = celery.Celery('task', broker='amqp://admin:admin@rabbit:5672//')


@app.task
def reset_dayly():
    print('Starting dayly reset', flush=True)
    dayly_reset()
    print('dayly reset complete', flush=True)


@app.task
def reset_weekly():
    print('Starting weekly reset', flush=True)
    weekly_reset()
    print('weekly reset complete', flush=True)


@app.task
def update_duc_balances():
    print('Starting DUC balance updating', flush=True)
    get_duc_balances()
    print('DUC balance updating complete', flush=True)


@app.task
def update_ducx_node_balandes():
    print('Starting DUCX node balance updating', flush=True)
    update_nodes()
    print('DUC node balance updating complete', flush=True)


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
        'task': 'task.update_ducx_node_balandes',
        'schedule': crontab(minute=0),
    }
}

