from django.db import models
from accounts.models import ClassGroup, Student, Teacher


class Course(models.Model):
    course_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    credits = models.IntegerField()
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    class_group = models.ForeignKey(ClassGroup, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.course_id} - {self.name}'


class Schedule(models.Model):
    DAYS = [('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'), ('Thu', 'Thursday'), ('Fri', 'Friday')]
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    day = models.CharField(max_length=3, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=30)

    def __str__(self):
        return f'{self.course.name} {self.day} {self.start_time}-{self.end_time}'


class Attendance(models.Model):
    STATUS = [('present', 'Present'), ('absent', 'Absent'), ('late', 'Late')]
    attendance_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS)
    note = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'course', 'date')

    def __str__(self):
        return f'{self.student.student_id} - {self.course.course_id} - {self.date} - {self.status}'


class Grade(models.Model):
    TYPES = [('exam', 'Exam'), ('quiz', 'Quiz'), ('homework', 'Homework'), ('project', 'Project')]
    value = models.FloatField()
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    grade_type = models.CharField(max_length=20, choices=TYPES, default='exam')
    date_recorded = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f'{self.student.student_id} - {self.course.course_id} - {self.value}'

# Create your models here.
