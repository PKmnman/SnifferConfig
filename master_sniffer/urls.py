from django.urls import path, include

import master_sniffer.views as views

urlpatterns = [
    path('event/', views.list_events, name='list_events'),
]