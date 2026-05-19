from django.contrib import admin
from .models import Attendance, Course, Grade, Schedule

admin.site.register(Course)
admin.site.register(Schedule)
admin.site.register(Attendance)
admin.site.register(Grade)
