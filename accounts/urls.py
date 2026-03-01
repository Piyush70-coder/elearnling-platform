from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/data/', views.admin_dashboard_data, name='admin_dashboard_data'),
    path('dashboard/admin/analytics-data/', views.admin_analytics_data, name='admin_analytics_data'),
    path('dashboard/admin/user-management/', views.user_management, name='user_management'),
    path('dashboard/admin/analytics/', views.analytics, name='analytics'),
    path('dashboard/admin/export-data/', views.export_data, name='export_data'),
    path('dashboard/admin/all-activity/', views.admin_all_activity, name='admin_all_activity'),
]