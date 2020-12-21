from django.contrib import admin
from ducatus_exchange.exchange_requests.models import DucatusUser, ExchangeRequest

admin.site.register(ExchangeRequest)
admin.site.register(DucatusUser)