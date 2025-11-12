from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

app_name = 'dashboards'

urlpatterns = [
    path('student/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/ajax/', views.AdminDashboardAjaxView.as_view(), name='admin_dashboard_ajax'),
    # Research data export endpoints
    path('export/research/', views.ResearchDataExportView.as_view(), name='export_research_data'),  # Default to Excel
    path('export/research/<str:format>/', views.ResearchDataExportView.as_view(), name='export_research_data_format'),
    # User growth data API
    path('api/user-growth/', csrf_exempt(views.UserGrowthDataView.as_view()), name='user_growth_data'),
]
