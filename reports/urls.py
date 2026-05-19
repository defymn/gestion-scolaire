from django.urls import path

from .views import report_view

urlpatterns = [
    path('admin-panel/reports/', report_view, name='admin_reports'),
]
