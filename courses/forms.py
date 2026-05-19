from django import forms
from django.forms import formset_factory

from accounts.models import Student
from .models import Attendance, Course, Grade


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'course', 'value', 'grade_type', 'comment']

    def clean(self):
        cleaned = super().clean()
        student = cleaned.get('student')
        course = cleaned.get('course')
        if student and course and student.class_group_id != course.class_group_id:
            raise forms.ValidationError("L'élève doit appartenir à la même classe / groupe que ce cours.")
        return cleaned

    def clean_value(self):
        value = self.cleaned_data['value']
        if value < 0 or value > 20:
            raise forms.ValidationError('Grade must be between 0 and 20.')
        return value

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            courses = Course.objects.filter(teacher=teacher)
            self.fields['course'].queryset = courses
            gids = courses.values_list('class_group_id', flat=True).distinct()
            self.fields['student'].queryset = Student.objects.filter(class_group_id__in=gids).distinct()


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['course', 'date']

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher)


class AttendanceRowForm(forms.Form):
    student_id = forms.IntegerField(widget=forms.HiddenInput())
    student_name = forms.CharField(disabled=True, required=False)
    status = forms.ChoiceField(choices=Attendance.STATUS)
    note = forms.CharField(widget=forms.Textarea(attrs={'rows': 1}), required=False)


AttendanceBulkFormSet = formset_factory(AttendanceRowForm, extra=0)


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_id', 'name', 'credits', 'teacher', 'class_group']
