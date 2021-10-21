from rest_framework.mixins import RetrieveModelMixin
from ducatus_exchange.payments.serializers import PaymentSerializer


class PaymentView(RetrieveModelMixin):

    serializer_class = PaymentSerializer
    lookup_field = 'tx_hash'
