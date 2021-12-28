import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from ducatus_exchange.serializers import FeedbackFormSerializer

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

logger = logging.getLogger('FeedbackForm')


class FeedbackForm(APIView):
    serializer_class = FeedbackFormSerializer

    @swagger_auto_schema(
        operation_description="post parameters to send feedback message",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['isWallet', 'subject', 'email', 'message'],
            properties={
                'isWallet': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'subject': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'message': openapi.Schema(type=openapi.TYPE_STRING)
            },),
        responses={200: 'OK'})

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.send_to_email()
        return Response(status=status.HTTP_200_OK)
