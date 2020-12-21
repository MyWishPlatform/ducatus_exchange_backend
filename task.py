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
app = celery.Celery('task', broker='amqp://')

@app.task
def reset_dayly():
    print('Starting dayly reset', flush=True)
    dayly_reset()
    print('dayly reset complete', flush= True)

@app.task
def reset_weekly():
    print('Starting weekly reset', flush=True)
    weekly_reset()
    print('weekly reset complete', flush=True)

app.conf.beat_schedule = {
    'dayly_task': {
        'task': 'task.reset_dayly',  # instead 'show'
        'schedule': crontab(hour=0),
    },
    'weekly_task': {
        'task': 'task.reset_weekly',  # instead 'show'
        'schedule': crontab(day_of_week=0),
    }
}

