from django.urls import path, include

from .views import PaymentView


urlpatterns = [
    path('<str:tx_hash>', PaymentView.as_view({'get': 'retrieve'})),
]