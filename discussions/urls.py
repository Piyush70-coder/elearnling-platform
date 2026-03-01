from django.urls import path
from . import views

app_name = 'discussions'

urlpatterns = [
    path('course/<int:course_id>/', views.discussion_list, name='list'),
    path('<int:discussion_id>/', views.discussion_detail, name='detail'),
    path('create/<int:course_id>/', views.create_discussion, name='create'),
    path('comment/<int:comment_id>/update/', views.update_comment, name='update_comment'),
    path('reaction/toggle/', views.toggle_reaction, name='toggle_reaction'),
    path('comment/<int:comment_id>/solution/', views.mark_as_solution, name='mark_solution'),
]