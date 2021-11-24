from rest_framework.viewsets import ModelViewSet


from ducatus_exchange.payments.models import Payment
from ducatus_exchange.payments.serializers import PaymentSerializer


class PaymentView(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    lookup_field = 'tx_hash'
