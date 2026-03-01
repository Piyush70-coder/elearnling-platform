from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    path('', views.assignment_list, name='assignment_list'),
    path('course/<int:course_id>/', views.assignment_list, name='course_assignments'),
    path('<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('submission/<int:submission_id>/', views.submission_detail, name='submission_detail'),
    path('submission/<int:submission_id>/status/', views.submission_status, name='submission_status'),
    path('test-result/<int:result_id>/', views.test_result, name='test_result'),
    path('submissions/', views.submission_list, name='submission_list'),
    path('<int:assignment_id>/uploads/', views.view_assignment_uploads, name='view_uploads'),
    path('<int:assignment_id>/manage-uploads/', views.manage_assignment_uploads, name='manage_uploads'),
    path('upload/<int:course_id>/', views.upload_assignment, name='upload_course_assignment'),
    path('uploads/', views.course_assignment_uploads, name='course_assignment_uploads'),
    path('uploads/course/<int:course_id>/', views.course_assignment_uploads, name='course_assignment_uploads_by_course'),
]
