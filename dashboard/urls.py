from django.urls import path

from .views import (
    parent_dashboard,
    parent_progress,
    role_home_redirect,
    student_attendance,
    student_dashboard,
    student_grades,
    student_schedule,
    student_setup_required,
)

urlpatterns = [
    path('', role_home_redirect, name='root_redirect'),
    path('student/', student_dashboard, name='student_dashboard'),
    path('student/setup/', student_setup_required, name='student_setup_required'),
    path('student/grades/', student_grades, name='student_grades'),
    path('student/attendance/', student_attendance, name='student_attendance'),
    path('student/schedule/', student_schedule, name='student_schedule'),
    path('parent/', parent_dashboard, name='parent_dashboard'),
    path('parent/progress/<int:student_id>/', parent_progress, name='parent_progress'),
]
