from django.contrib import admin
from ducatus_exchange.bot.models import BotSub, BotSwapMessage

admin.site.register(BotSwapMessage)
admin.site.register(BotSub)