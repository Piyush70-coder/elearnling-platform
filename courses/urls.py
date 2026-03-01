from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('create/', views.create_course, name='create_course'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('<int:course_id>/unenroll/', views.unenroll_course, name='unenroll_course'),
    path('<int:course_id>/lectures/', views.manage_lectures, name='manage_lectures'),
    path('lectures/create/<int:course_id>/', views.create_lecture, name='create_lecture'),
    path('lectures/<int:lecture_id>/', views.view_lecture, name='view_lecture'),
    path('lectures/<int:lecture_id>/edit/', views.edit_lecture, name='edit_lecture'),
    path('lectures/<int:lecture_id>/delete/', views.delete_lecture, name='delete_lecture'),
    path('lectures/<int:lecture_id>/progress/', views.update_lecture_progress, name='update_lecture_progress'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('instructor/courses/', views.instructor_courses, name='instructor_courses'),
    path('student/courses/', views.student_courses, name='student_courses'),
    
    # Quiz URLs
    path('<int:course_id>/quizzes/', views.quiz_list, name='quiz_list'),
    path('<int:course_id>/quizzes/create/', views.create_quiz, name='create_quiz'),
    path('quizzes/<int:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('quizzes/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('quizzes/<int:quiz_id>/results/<int:attempt_id>/', views.quiz_results, name='quiz_results'),
    
    # Review and Comment URLs
    path('<int:course_id>/review/', views.add_review, name='add_review'),
    path('lectures/<int:lecture_id>/comment/', views.add_comment, name='add_comment'),
]