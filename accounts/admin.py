from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ClassGroup, Parent, Student, Teacher, User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('role',)}),)
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')


admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Parent)
admin.site.register(ClassGroup)
