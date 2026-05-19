from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import Parent, Student
from courses.models import Attendance, Grade, Schedule


@login_required
def role_home_redirect(request):
    # Always treat Django superusers/staff as admins in this app.
    if request.user.is_superuser or request.user.is_staff:
        return redirect('admin_panel_dashboard')
    if request.user.role == 'admin':
        return redirect('admin_panel_dashboard')
    if request.user.role == 'teacher':
        return redirect('teacher_dashboard')
    if request.user.role == 'student':
        return redirect('student_dashboard')
    if request.user.role == 'parent':
        return redirect('parent_dashboard')
    return redirect('login')


@login_required
@role_required('student')
def student_dashboard(request):
    student = Student.objects.filter(user=request.user).first()
    if not student:
        messages.error(request, 'Student profile not found. Please complete your student profile first.')
        return redirect('student_setup_required')
    avg_grade = Grade.objects.filter(student=student).aggregate(avg=Avg('value'))['avg']
    total_attendance = Attendance.objects.filter(student=student).count()
    present_attendance = Attendance.objects.filter(student=student, status='present').count()
    attendance_percent = (present_attendance / total_attendance * 100) if total_attendance else 0
    next_class = Schedule.objects.filter(course__class_group=student.class_group).select_related('course').order_by('day', 'start_time').first()
    return render(
        request,
        'student/dashboard.html',
        {'avg_grade': avg_grade, 'attendance_percent': attendance_percent, 'next_class': next_class},
    )


@login_required
@role_required('student')
def student_setup_required(request):
    return render(request, 'student/setup_required.html')


@login_required
@role_required('student')
def student_grades(request):
    student = get_object_or_404(Student, user=request.user)
    grades = Grade.objects.filter(student=student).select_related('course').order_by('course__name')
    grouped = {}
    for grade in grades:
        grouped.setdefault(grade.course, []).append(grade)
    grouped_data = []
    for course, course_grades in grouped.items():
        avg = Grade.objects.filter(student=student, course=course).aggregate(avg=Avg('value'))['avg']
        grouped_data.append({'course': course, 'grades': course_grades, 'average': avg})
    return render(request, 'student/grades.html', {'grouped_data': grouped_data})


@login_required
@role_required('student')
def student_attendance(request):
    student = get_object_or_404(Student, user=request.user)
    records = Attendance.objects.filter(student=student).select_related('course').order_by('-date')
    return render(request, 'student/attendance.html', {'records': records})


@login_required
@role_required('student')
def student_schedule(request):
    student = get_object_or_404(Student, user=request.user)
    schedules = Schedule.objects.filter(course__class_group=student.class_group).select_related('course').order_by('start_time')
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    return render(request, 'student/schedule.html', {'schedules': schedules, 'days': days})


@login_required
@role_required('parent')
def parent_dashboard(request):
    parent = get_object_or_404(Parent, user=request.user)
    child_cards = []
    for child in parent.children.select_related('user'):
        avg_grade = Grade.objects.filter(student=child).aggregate(avg=Avg('value'))['avg']
        total = Attendance.objects.filter(student=child).count()
        present = Attendance.objects.filter(student=child, status='present').count()
        attendance_percent = (present / total * 100) if total else 0
        child_cards.append({'child': child, 'avg_grade': avg_grade, 'attendance_percent': attendance_percent})
    return render(request, 'parent/dashboard.html', {'child_cards': child_cards})


@login_required
@role_required('parent')
def parent_progress(request, student_id):
    parent = get_object_or_404(Parent, user=request.user)
    child = get_object_or_404(parent.children.all(), pk=student_id)
    grades = Grade.objects.filter(student=child).select_related('course').order_by('-date_recorded')
    attendance = Attendance.objects.filter(student=child).select_related('course').order_by('-date')
    return render(request, 'parent/progress.html', {'child': child, 'grades': grades, 'attendance': attendance})
