"""ducatus_exchange URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from ducatus_exchange.views import FeedbackForm
from ducatus_exchange.exchange_requests.views import ValidateDucatusAddress, register_voucher_in_lottery
from ducatus_exchange.lottery.views import LotteryViewSet, LotteryPlayerViewSet, lottery_participants, \
    get_lottery_info, register_payments_manually
from ducatus_exchange.quantum.views import get_charge, add_charge, change_charge_status
from ducatus_exchange.stats.views import DucxWalletsViewSet

schema_view = get_schema_view(
    openapi.Info(
        title="Ducatus Widget API",
        default_version='v1',
        description="API for widget backend",
        contact=openapi.Contact(email="ephdtrg@mintyclouds.in"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter(trailing_slash=True)
router.register(r'lotteries', LotteryViewSet)
router.register(r'lotteries_players', LotteryPlayerViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', schema_view),
    url(r'^api/v1/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^api/v1/swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^api/v1/redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    url(r'^api/v1/rates/', include('ducatus_exchange.rates.urls')),
    url(r'^api/v1/transfers/', include('ducatus_exchange.transfers.urls')),
    url(r'^api/v1/exchange/', include('ducatus_exchange.exchange_requests.urls')),
    url(r'api/v1/validate_ducatus_address/', ValidateDucatusAddress.as_view(), name='validate-ducatus-address'),
    url(r'api/v1/send_ducatus_feedback/', FeedbackForm.as_view(), name='send-ducatus-feedback'),
    url(r'api/v1/lottery_participants/', lottery_participants),
    url(r'^api/v1/get_lotteries_info', get_lottery_info),
    url(r'api/v1/get_charge/', get_charge),
    url(r'api/v1/add_charge/', add_charge),
    url(r'api/v1/change_charge_status/', change_charge_status),
    url(r'api/v1/register_payments_manually/', register_payments_manually),
    url(r'api/v1/register_voucher_in_lottery/', register_voucher_in_lottery),
    url(r'^api/v1/', include(router.urls)),
    url(r'^api/v1/payments/', include('ducatus_exchange.payments.urls'))
]
