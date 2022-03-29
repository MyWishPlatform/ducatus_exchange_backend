from django.urls import path

from ducatus_exchange.scanner.views import AddressesToScan, PaymentHandler, EventsForScann, ERC20PaymentHandler


urlpatterns = [
    path('scanner/', AddressesToScan.as_view(),),
    path('contracts/', EventsForScann.as_view()),
    path('register-payment/', PaymentHandler.as_view()),
    path('register-events/', ERC20PaymentHandler.as_view()),
]
