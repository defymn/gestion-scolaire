import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import HttpResponse
from django.shortcuts import render

from accounts.decorators import role_required
from accounts.models import ClassGroup, Student
from courses.models import Attendance


@login_required
@role_required('admin')
def report_view(request):
    class_rows = []
    for class_group in ClassGroup.objects.all().order_by('name'):
        students = Student.objects.filter(class_group=class_group)
        avg_grade = (
            Student.objects.filter(class_group=class_group)
            .aggregate(avg=Avg('grade__value'))
            .get('avg')
        )
        total_attendance = Attendance.objects.filter(student__in=students).count()
        present_attendance = Attendance.objects.filter(student__in=students, status='present').count()
        attendance_pct = (present_attendance / total_attendance * 100) if total_attendance else 0
        class_rows.append(
            {
                'class_name': str(class_group),
                'avg_grade': round(avg_grade, 2) if avg_grade is not None else None,
                'attendance_pct': round(attendance_pct, 2),
                'students_count': students.count(),
            }
        )

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="class_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Class', 'Students', 'Average Grade', 'Attendance %'])
        for row in class_rows:
            writer.writerow([row['class_name'], row['students_count'], row['avg_grade'] or 'N/A', row['attendance_pct']])
        return response

    return render(request, 'admin_panel/reports.html', {'class_rows': class_rows})
