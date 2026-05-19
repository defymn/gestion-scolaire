from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

from .college_demo import assign_college_demo_course_teachers
from .models import ClassGroup, Parent, Student, Teacher, User


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Invalid username or password.')

        return cleaned_data

    def get_user(self):
        return self.user_cache


class UserCreateForm(UserCreationForm):
    class_group = forms.ModelChoiceField(queryset=ClassGroup.objects.all(), required=False)
    student_id = forms.CharField(max_length=20, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    teacher_id = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2',
            'role',
        ]

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == 'student':
            if not cleaned_data.get('student_id'):
                self.add_error('student_id', 'Student ID is required for student role.')
            if not cleaned_data.get('date_of_birth'):
                self.add_error('date_of_birth', 'Date of birth is required for student role.')
        if role == 'teacher' and not cleaned_data.get('teacher_id'):
            self.add_error('teacher_id', 'Teacher ID is required for teacher role.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=commit)
        role = self.cleaned_data['role']
        if role == 'student':
            class_group = self.cleaned_data.get('class_group')
            if not class_group:
                class_group = ClassGroup.objects.filter(name='1AC — Groupe 1').order_by('-year').first() or ClassGroup.objects.order_by('id').first()
            Student.objects.update_or_create(
                user=user,
                defaults={
                    'student_id': self.cleaned_data['student_id'],
                    'date_of_birth': self.cleaned_data['date_of_birth'],
                    'class_group': class_group,
                },
            )
        elif role == 'teacher':
            Teacher.objects.update_or_create(user=user, defaults={'teacher_id': self.cleaned_data['teacher_id']})
            assign_college_demo_course_teachers()
        elif role == 'parent':
            Parent.objects.get_or_create(user=user)
        return user


class UserUpdateForm(forms.ModelForm):
    class_group = forms.ModelChoiceField(queryset=ClassGroup.objects.all(), required=False)
    student_id = forms.CharField(max_length=20, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    teacher_id = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance
        if hasattr(user, 'student_profile'):
            self.fields['student_id'].initial = user.student_profile.student_id
            self.fields['date_of_birth'].initial = user.student_profile.date_of_birth
            self.fields['class_group'].initial = user.student_profile.class_group
        if hasattr(user, 'teacher_profile'):
            self.fields['teacher_id'].initial = user.teacher_profile.teacher_id

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == 'student':
            if not cleaned_data.get('student_id'):
                self.add_error('student_id', 'Student ID is required for student role.')
            if not cleaned_data.get('date_of_birth'):
                self.add_error('date_of_birth', 'Date of birth is required for student role.')
        if role == 'teacher' and not cleaned_data.get('teacher_id'):
            self.add_error('teacher_id', 'Teacher ID is required for teacher role.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=commit)
        role = self.cleaned_data['role']
        Student.objects.filter(user=user).delete() if role != 'student' else None
        Teacher.objects.filter(user=user).delete() if role != 'teacher' else None
        Parent.objects.filter(user=user).delete() if role != 'parent' else None
        if role == 'student':
            class_group = self.cleaned_data.get('class_group')
            if not class_group:
                class_group = ClassGroup.objects.filter(name='1AC — Groupe 1').order_by('-year').first() or ClassGroup.objects.order_by('id').first()
            Student.objects.update_or_create(
                user=user,
                defaults={
                    'student_id': self.cleaned_data['student_id'],
                    'date_of_birth': self.cleaned_data['date_of_birth'],
                    'class_group': class_group,
                },
            )
        elif role == 'teacher':
            Teacher.objects.update_or_create(user=user, defaults={'teacher_id': self.cleaned_data['teacher_id']})
            assign_college_demo_course_teachers()
        elif role == 'parent':
            Parent.objects.get_or_create(user=user)
        return user


class SignupForm(UserCreateForm):
    """
    Public registration form.
    Restricts role selection to non-admin roles.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Never allow self-registering as admin.
        if 'role' in self.fields:
            self.fields['role'].choices = [
                ('student', 'Student'),
                ('teacher', 'Teacher'),
                ('parent', 'Parent'),
            ]
