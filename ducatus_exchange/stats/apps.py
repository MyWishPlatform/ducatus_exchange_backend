from django.apps import AppConfig

from ducatus_exchange import stats


class StatsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ducatus_exchange.stats'
