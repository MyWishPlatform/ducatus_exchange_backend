from django.conf.urls import url
from django.urls import path
from ducatus_exchange.exchange_requests.views import ExchangeRequestView, total_id_count

urlpatterns = [
    path('total/', total_id_count),
    url(r'^$', ExchangeRequestView.as_view(), name='create-exchange-request'),
]