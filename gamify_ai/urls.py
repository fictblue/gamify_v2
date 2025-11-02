"""
URL configuration for gamify_ai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from dashboards.api_views import top_users_success_rate, qlearning_logs_api, download_qtable

app_name = 'gamify_ai'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboards.urls')),
    path('quizzes/', include('quizzes.urls')),
    path('qlearning/', include('qlearning.urls')),
    
    # API endpoints for admin dashboard
    path('api/top-users-success-rate/', top_users_success_rate, name='api_top_users'),
    path('api/qlearning-logs/', qlearning_logs_api, name='api_qlearning_logs'),
    path('api/download-qtable/', download_qtable, name='api_download_qtable'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
