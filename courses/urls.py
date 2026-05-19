from django.urls import path

from .views import (
    attendance_create_view,
    attendance_list_view,
    attendance_update_view,
    grade_create_view,
    grade_list_view,
    grade_update_view,
    teacher_courses,
    teacher_dashboard,
    teacher_students,
)

urlpatterns = [
    path('teacher/', teacher_dashboard, name='teacher_dashboard'),
    path('teacher/courses/', teacher_courses, name='teacher_courses'),
    path('teacher/students/', teacher_students, name='teacher_students'),
    path('teacher/grades/', grade_list_view, name='teacher_grades'),
    path('teacher/grades/add/', grade_create_view, name='teacher_grade_add'),
    path('teacher/grades/<int:pk>/edit/', grade_update_view, name='teacher_grade_edit'),
    path('teacher/attendance/', attendance_list_view, name='teacher_attendance'),
    path('teacher/attendance/add/', attendance_create_view, name='teacher_attendance_add'),
    path('teacher/attendance/<int:pk>/edit/', attendance_update_view, name='teacher_attendance_edit'),
]
