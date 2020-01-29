from django.conf.urls import url

from ducatus_exchange.exchange_requests.views import ExchangeRequest

urlpatterns = [
    url(r'^$', ExchangeRequest.as_view(), name='create-exchange-request'),
]