from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLES = [
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    ]
    role = models.CharField(max_length=20, choices=ROLES, default='student')

    def __str__(self):
        return f'{self.username} ({self.role})'


class ClassGroup(models.Model):
    name = models.CharField(max_length=50)
    year = models.IntegerField(default=2026)

    def __str__(self):
        return f'{self.name} ({self.year})'


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    class_group = models.ForeignKey(ClassGroup, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.student_id} - {self.user.get_full_name() or self.user.username}'


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f'{self.teacher_id} - {self.user.get_full_name() or self.user.username}'


class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    children = models.ManyToManyField(Student, related_name='parents', blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

# Create your models here.
