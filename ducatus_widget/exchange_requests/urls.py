from django.conf.urls import url

from ducatus_widget.exchange_requests.views import ExchangeRequest

urlpatterns = [
    url(r'^$', ExchangeRequest.as_view(), name='create-exchange-request'),
]