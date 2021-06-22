import statistics

from django.conf.urls import url
from django.urls import path

from . import views

app_name = "stats"
# app_name will help us do a reverse look-up latter.
urlpatterns = [
    path('statistics/<str:currency>/<int:days>', views.StatsHandler.as_view()),
    # path('statistics/ducx_wallets', views.DucxWalletsHandler.as_view({'get': 'list'})),
    path('statistics/duc_wallets/', views.DucWalletsView.as_view()),
    path('statistics/<str:currency>_wallets/csv', views.DucxWalletsToCSV.as_view()),
]
