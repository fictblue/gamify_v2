from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    # Admin URLs
    path('admin/', views.AdminQuizListView.as_view(), name='admin_quiz_list'),
    path('admin/create/', views.AdminQuizCreateView.as_view(), name='admin_quiz_create'),
    path('admin/edit/<int:question_id>/', views.AdminQuizEditView.as_view(), name='admin_quiz_edit'),
    path('admin/delete/<int:question_id>/', views.AdminQuizDeleteView.as_view(), name='admin_quiz_delete'),

    # Student URLs
    path('student/', views.StudentQuizListView.as_view(), name='student_quiz_list'),
    path('student/take/<int:question_id>/', views.StudentQuizTakeView.as_view(), name='student_quiz_take'),
    path('student/get-next/', views.get_next_question, name='get_next_question'),
    path('student/hint/<int:question_id>/', views.get_question_hint, name='get_question_hint'),
    path('submit/', views.submit_answer, name='submit_answer'),

    # Debug URLs
    path('debug/user-constraints/', views.debug_user_constraints, name='debug_user_constraints'),
]
