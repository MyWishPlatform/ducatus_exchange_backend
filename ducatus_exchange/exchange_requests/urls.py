from django.conf.urls import url
from django.urls import path
from ducatus_exchange.exchange_requests.views import (
    ExchangeRequestView,
    ExchangeStatusView,
    total_id_count,
    status_check
)

urlpatterns = [
    path('total/', total_id_count),
    path('status/', status_check),
    url(r'^$', ExchangeRequestView.as_view(), name='create-exchange-request'),
    url(r'^exchange_status', ExchangeStatusView.as_view()),
]
