from django.urls import path

from ducatus_exchange.scanner.views import AddressesToScan, PaymentHandler, EventsForScann, ERC20PaymentHandler


urlpatterns = [
    path('get-addresses', AddressesToScan.as_view(),),
    path('get-contracts', EventsForScann.as_view()),
    path('register-payments', PaymentHandler.as_view()),
    path('register-events', ERC20PaymentHandler.as_view()),
]
