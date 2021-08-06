from django.contrib import admin

# Register your models here.
from ducatus_exchange.stats.models import StatisticsTransfer

admin.site.register(StatisticsTransfer)
