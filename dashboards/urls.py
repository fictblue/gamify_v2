from django.urls import path
from . import views

app_name = 'dashboards'

urlpatterns = [
    path('student/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/ajax/', views.AdminDashboardAjaxView.as_view(), name='admin_dashboard_ajax'),
]
