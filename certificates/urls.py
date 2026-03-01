from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('student/', views.student_certificates, name='student_list'),
    path('course/<int:course_id>/', views.course_certificates, name='course_list'),
    path('generate/<int:enrollment_id>/', views.generate_certificate, name='generate'),
    path('view/<uuid:certificate_id>/', views.view_certificate, name='view'),
    path('download/<uuid:certificate_id>/', views.download_certificate, name='download'),
    path('verify/<uuid:certificate_id>/', views.verify_certificate, name='verify'),
    path('request/<int:enrollment_id>/', views.request_certificate, name='request_certificate'),
]