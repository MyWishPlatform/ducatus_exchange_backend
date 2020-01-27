from django.conf.urls import url

from ducatus_widget.rates.views import RateRequest

urlpatterns = [
    url(r'get', RateRequest.as_view())
]