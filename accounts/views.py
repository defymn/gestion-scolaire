from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import FormView

from accounts.decorators import role_required
from courses.forms import CourseForm
from courses.models import Course
from .forms import LoginForm, SignupForm, UserCreateForm, UserUpdateForm
from .models import ClassGroup, User


class LoginView(FormView):
    template_name = 'auth/login.html'
    form_class = LoginForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        # Superusers/staff should always land in the admin panel.
        if user.is_superuser or user.is_staff:
            return redirect('admin_panel_dashboard')
        role_to_route = {
            'admin': 'admin_panel_dashboard',
            'teacher': 'teacher_dashboard',
            'student': 'student_dashboard',
            'parent': 'parent_dashboard',
        }
        return redirect(role_to_route[user.role])


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')


class SignupView(FormView):
    template_name = 'auth/signup.html'
    form_class = SignupForm

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Account created successfully.')
        return redirect('root_redirect')


@login_required
@role_required('admin')
def admin_panel_dashboard(request):
    return render(request, 'admin_panel/dashboard.html')


@login_required
@role_required('admin')
def user_list_view(request):
    query = request.GET.get('q', '').strip()
    users = User.objects.all().order_by('username')
    if query:
        users = users.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(username__icontains=query)
            | Q(role__icontains=query)
        )
    paginator = Paginator(users, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_panel/users.html', {'page_obj': page_obj, 'query': query})


@login_required
@role_required('admin')
def user_create_view(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            return redirect('admin_users')
    else:
        form = UserCreateForm()
    return render(request, 'admin_panel/user_form.html', {'form': form, 'title': 'Add User'})


@login_required
@role_required('admin')
def user_update_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('admin_users')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'admin_panel/user_form.html', {'form': form, 'title': 'Edit User'})


@login_required
@role_required('admin')
def user_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
    return redirect('admin_users')


@login_required
@role_required('admin')
def class_list_view(request):
    classes = ClassGroup.objects.all().order_by('-year', 'name')
    return render(request, 'admin_panel/classes.html', {'classes': classes})


@login_required
@role_required('admin')
def class_create_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        year = request.POST.get('year', '').strip()
        if name and year.isdigit():
            ClassGroup.objects.create(name=name, year=int(year))
            messages.success(request, 'Class group created.')
            return redirect('admin_classes')
        messages.error(request, 'Please provide a valid class name and year.')
    return render(request, 'admin_panel/class_form.html', {'title': 'Add Class Group'})


@login_required
@role_required('admin')
def class_update_view(request, pk):
    class_group = get_object_or_404(ClassGroup, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        year = request.POST.get('year', '').strip()
        if name and year.isdigit():
            class_group.name = name
            class_group.year = int(year)
            class_group.save()
            messages.success(request, 'Class group updated.')
            return redirect('admin_classes')
        messages.error(request, 'Please provide a valid class name and year.')
    return render(request, 'admin_panel/class_form.html', {'title': 'Edit Class Group', 'class_group': class_group})


@login_required
@role_required('admin')
def class_delete_view(request, pk):
    class_group = get_object_or_404(ClassGroup, pk=pk)
    if request.method == 'POST':
        class_group.delete()
        messages.success(request, 'Class group deleted.')
    return redirect('admin_classes')


@login_required
@role_required('admin')
def subject_list_view(request):
    subjects = Course.objects.select_related('teacher__user', 'class_group').all().order_by('name')
    return render(request, 'admin_panel/subjects.html', {'subjects': subjects})


@login_required
@role_required('admin')
def subject_create_view(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject created.')
            return redirect('admin_subjects')
    else:
        form = CourseForm()
    return render(request, 'admin_panel/subject_form.html', {'form': form, 'title': 'Add Subject'})


@login_required
@role_required('admin')
def subject_update_view(request, pk):
    subject = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated.')
            return redirect('admin_subjects')
    else:
        form = CourseForm(instance=subject)
    return render(request, 'admin_panel/subject_form.html', {'form': form, 'title': 'Edit Subject'})


@login_required
@role_required('admin')
def subject_delete_view(request, pk):
    subject = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted.')
    return redirect('admin_subjects')
