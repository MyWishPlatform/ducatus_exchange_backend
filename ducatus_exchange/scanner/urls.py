from django.urls import path

from ducatus_exchange.scanner.views import AddressesToScan, PaymentHandler


urlpatterns = [
    path('scanner/<str:network>', AddressesToScan.as_view(),),
    path('payment', PaymentHandler.as_view())
]
