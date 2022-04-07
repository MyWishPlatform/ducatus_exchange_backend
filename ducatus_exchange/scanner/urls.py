from django.urls import path

from ducatus_exchange.scanner.views import AddressesToScan, PaymentHandler


urlpatterns = [
    path('get-addresses', AddressesToScan.as_view(),),
    path('register-payments', PaymentHandler.as_view()),
]
