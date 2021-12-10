from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ducatus_exchange.settings import IS_TESTNET_PAYMENTS

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ducatus_exchange.payments.models import Payment
from ducatus_exchange.payments.serializers import (
    PaymentSerializer,
    PaymentStatusSerializer
)


class PaymentView(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    lookup_field = 'tx_hash'


class PaymentStatusView(APIView):

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'tx_hashes': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING))}),
        required=['tx_hashes'],
        responses={200: PaymentStatusSerializer()})
    def post(self, request):
        txs = Payment.objects.filter(tx_hash__in=request.data.get('tx_hashes'))
        serializer = PaymentStatusSerializer(txs, many=True)
        return Response({
            'is_testnet': IS_TESTNET_PAYMENTS,
            'payments': serializer.data}, status.HTTP_200_OK)
