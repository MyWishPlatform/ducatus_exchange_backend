import datetime as dt

from dateutil.relativedelta import relativedelta
from django.db import models


class CltvDetails(models.Model):
    withdrawn = models.BooleanField(default=False)
    lock_time = models.BigIntegerField()
    redeem_script = models.TextField()
    locked_duc_address = models.CharField(max_length=50)
    user_public_key = models.CharField(max_length=80)
    frozen_at = models.DateTimeField()
    private_path = models.CharField(max_length=20, default='')

    def total_days(self):
        start = self.frozen_at.replace(microsecond=0, tzinfo=None)
        finish_timestamp = self.lock_time
        finish = dt.datetime.fromtimestamp(finish_timestamp)
        timedelta = finish - start
        days = timedelta.days
        return days

    @staticmethod
    def month_to_days(months, start_date=None):
        start_date = start_date if start_date else dt.datetime.now().replace(microsecond=0)
        lock_date = start_date + relativedelta(months=months)
        days = (lock_date - start_date).days
        return days
