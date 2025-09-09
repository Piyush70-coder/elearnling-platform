from django.urls import path
from . import views

app_name = 'compiler'

urlpatterns = [
    path('', views.compiler_view, name='compiler'),
    path('execute/', views.execute_code, name='execute_code'),
    path('result/<int:execution_id>/', views.get_execution_result, name='get_result'),
    path('history/', views.execution_history, name='history'),
    path('template/<str:language>/', views.get_code_template, name='get_template'),
]