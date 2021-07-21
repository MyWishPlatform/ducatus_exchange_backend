from django.urls import path
from django.conf.urls import include
from rest_framework.routers import DefaultRouter

from . import views

app_name = "stats"
# app_name will help us do a reverse look-up latter.

stats_router = DefaultRouter(trailing_slash=True)
stats_router.register(r'ducx_wallets', views.DucxWalletsViewSet)

urlpatterns = [
    path('statistics/<str:currency>/<int:days>', views.StatsHandler.as_view()),
    path('statistics/duc_wallets/', views.DucWalletsView.as_view()),
    path('statistics/', include(stats_router.urls)),
    path('statistics/<str:currency>_wallets/csv', views.DucxWalletsToCSV.as_view()),
    path('statistics/daily_swap/duc_to_ducx/', views.DucToDucxSwap.as_view()),
    path('statistics/daily_swap/ducx_to_duc/', views.DucxToDucSwap.as_view()),
    path('statistics/wallets_total', views.StatisticsTotals.as_view())
]
