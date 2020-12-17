from django.conf.urls import url

from ducatus_exchange.transfers.views import CheckLimitView

urlpatterns = [
    url(r'^$', CheckLimitView.as_view(), name='check swap limits'),
]