from ducatus_exchange.exchange_requests.models import ExchangeRequest


def dayly_reset():
    ExchangeRequest.objects.all().update(dayly_swap=0)


def weekly_reset():
    ExchangeRequest.objects.all().update(weekly_swap=0)
