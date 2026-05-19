from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import Student, Teacher
from .forms import AttendanceBulkFormSet, AttendanceForm, GradeForm
from .models import Attendance, Course, Grade


def _teacher_courses_queryset(teacher):
    return Course.objects.filter(teacher=teacher).select_related('class_group').order_by('class_group__name', 'name')


def _teacher_students_queryset(teacher):
    """Élèves des classes (groupes) où ce prof enseigne au moins un cours."""
    gids = _teacher_courses_queryset(teacher).values_list('class_group_id', flat=True).distinct()
    return (
        Student.objects.filter(class_group_id__in=gids)
        .select_related('user', 'class_group')
        .distinct()
        .order_by('class_group__name', 'user__last_name', 'user__first_name', 'user__username')
    )


@login_required
@role_required('teacher')
def teacher_dashboard(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    courses = _teacher_courses_queryset(teacher)
    students_qs = _teacher_students_queryset(teacher)
    students_count = students_qs.count()
    grades_this_month = Grade.objects.filter(
        course__in=courses, date_recorded__year=date.today().year, date_recorded__month=date.today().month
    ).count()
    pending_grades = students_count - grades_this_month
    my_courses = courses.annotate(student_count=Count('class_group__student', distinct=True))
    return render(
        request,
        'teacher/dashboard.html',
        {
            'students_count': students_count,
            'courses_count': courses.count(),
            'grades_this_month': grades_this_month,
            'pending_grades': max(pending_grades, 0),
            'my_courses': my_courses,
        },
    )


@login_required
@role_required('teacher')
def teacher_courses(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    courses = _teacher_courses_queryset(teacher).annotate(student_count=Count('class_group__student', distinct=True))
    return render(request, 'teacher/courses.html', {'courses': courses})


@login_required
@role_required('teacher')
def teacher_students(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    students = _teacher_students_queryset(teacher)
    return render(request, 'teacher/students.html', {'students': students})


@login_required
@role_required('teacher')
def grade_list_view(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    course_id = request.GET.get('course')
    grades = Grade.objects.filter(course__teacher=teacher).select_related('student__user', 'course').order_by('-date_recorded')
    if course_id:
        try:
            grades = grades.filter(course_id=int(course_id))
        except ValueError:
            pass
    courses = Course.objects.filter(teacher=teacher)
    return render(request, 'teacher/grades.html', {'grades': grades, 'courses': courses, 'selected_course': course_id})


@login_required
@role_required('teacher')
def grade_create_view(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    if request.method == 'POST':
        form = GradeForm(request.POST, teacher=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grade created successfully.')
            return redirect('teacher_grades')
    else:
        form = GradeForm(teacher=teacher)
    return render(request, 'teacher/grade_form.html', {'form': form, 'title': 'Add Grade'})


@login_required
@role_required('teacher')
def grade_update_view(request, pk):
    teacher = get_object_or_404(Teacher, user=request.user)
    grade = get_object_or_404(Grade, pk=pk, course__teacher=teacher)
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=grade, teacher=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grade updated successfully.')
            return redirect('teacher_grades')
    else:
        form = GradeForm(instance=grade, teacher=teacher)
    return render(request, 'teacher/grade_form.html', {'form': form, 'title': 'Edit Grade'})


@login_required
@role_required('teacher')
def attendance_list_view(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    attendance_records = Attendance.objects.filter(course__teacher=teacher).select_related('student__user', 'course').order_by('-date')
    return render(request, 'teacher/attendance.html', {'attendance_records': attendance_records})


@login_required
@role_required('teacher')
def attendance_create_view(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    if request.method == 'POST':
        form = AttendanceForm(request.POST, teacher=teacher)
        if 'load_students' in request.POST and form.is_valid():
            course = form.cleaned_data['course']
            students = Student.objects.filter(class_group=course.class_group).select_related('user')
            initial = [{'student_id': s.id, 'student_name': s.user.get_full_name() or s.user.username, 'status': 'present'} for s in students]
            formset = AttendanceBulkFormSet(initial=initial, prefix='rows')
            return render(request, 'teacher/attendance_form.html', {'form': form, 'formset': formset, 'title': 'Mark Attendance'})
        formset = AttendanceBulkFormSet(request.POST, prefix='rows')
        if form.is_valid() and formset.is_valid():
            course = form.cleaned_data['course']
            attendance_date = form.cleaned_data['date']
            for row in formset:
                student = Student.objects.get(pk=row.cleaned_data['student_id'])
                Attendance.objects.update_or_create(
                    student=student,
                    course=course,
                    date=attendance_date,
                    defaults={'status': row.cleaned_data['status'], 'note': row.cleaned_data.get('note', '')},
                )
            messages.success(request, 'Attendance saved.')
            return redirect('teacher_attendance')
    else:
        form = AttendanceForm(teacher=teacher)
        formset = AttendanceBulkFormSet(prefix='rows')
    return render(request, 'teacher/attendance_form.html', {'form': form, 'formset': formset, 'title': 'Mark Attendance'})


@login_required
@role_required('teacher')
def attendance_update_view(request, pk):
    teacher = get_object_or_404(Teacher, user=request.user)
    record = get_object_or_404(Attendance, pk=pk, course__teacher=teacher)
    if request.method == 'POST':
        status = request.POST.get('status')
        note = request.POST.get('note', '')
        if status in {'present', 'absent', 'late'}:
            record.status = status
            record.note = note
            record.save()
            messages.success(request, 'Attendance updated.')
            return redirect('teacher_attendance')
    return render(request, 'teacher/attendance_form.html', {'record': record, 'title': 'Edit Attendance'})
