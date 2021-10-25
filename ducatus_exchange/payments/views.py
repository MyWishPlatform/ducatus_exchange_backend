from rest_framework.generics import RetrieveAPIView

from ducatus_exchange.payments.serializers import PaymentSerializer


class PaymentView(RetrieveAPIView):

    serializer_class = PaymentSerializer
    lookup_field = 'tx_hash'
