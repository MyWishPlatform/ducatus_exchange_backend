from django.conf.urls import url

from ducatus_exchange.rates.views import RateRequest

urlpatterns = [
    url(r'^$', RateRequest.as_view(), name='get-rates'),
]
