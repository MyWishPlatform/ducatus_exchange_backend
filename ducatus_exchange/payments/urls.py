from django.urls import path, include

from .views import PaymentView, PaymentStatusView


urlpatterns = [
    path('<str:tx_hash>', PaymentView.as_view({'get': 'retrieve'})),
    path('get_status/', PaymentStatusView.as_view(), name='payments-get-status-list')
]
