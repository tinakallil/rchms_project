                                             
from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('dashboard/', views.dashboard, name='dashboard'),

                        
    path('repair-requests/', views.repair_request_list, name='repair_request_list'),
    path('repair-requests/new/', views.repair_request_create, name='repair_request_create'),
    path('repair-requests/<int:pk>/', views.repair_request_detail, name='repair_request_detail'),
    path('repair-requests/<int:pk>/edit/', views.repair_request_update, name='repair_request_update'),
    path('repair-requests/<int:pk>/delete/', views.repair_request_delete, name='repair_request_delete'),
    path('repair-requests/<int:pk>/updates/', views.repair_request_add_update, name='repair_request_add_update'),

                             
    path('notifications/', views.notifications, name='notifications'),
    path('reports/community/<int:pk>/', views.community_report, name='community_report'),
]
