from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    SignupView,
    admin_panel_dashboard,
    class_create_view,
    class_delete_view,
    class_list_view,
    class_update_view,
    subject_create_view,
    subject_delete_view,
    subject_list_view,
    subject_update_view,
    user_create_view,
    user_delete_view,
    user_list_view,
    user_update_view,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('admin-panel/', admin_panel_dashboard, name='admin_panel_dashboard'),
    path('admin-panel/users/', user_list_view, name='admin_users'),
    path('admin-panel/users/add/', user_create_view, name='admin_user_add'),
    path('admin-panel/users/<int:pk>/edit/', user_update_view, name='admin_user_edit'),
    path('admin-panel/users/<int:pk>/delete/', user_delete_view, name='admin_user_delete'),
    path('admin-panel/classes/', class_list_view, name='admin_classes'),
    path('admin-panel/classes/add/', class_create_view, name='admin_class_add'),
    path('admin-panel/classes/<int:pk>/edit/', class_update_view, name='admin_class_edit'),
    path('admin-panel/classes/<int:pk>/delete/', class_delete_view, name='admin_class_delete'),
    path('admin-panel/subjects/', subject_list_view, name='admin_subjects'),
    path('admin-panel/subjects/add/', subject_create_view, name='admin_subject_add'),
    path('admin-panel/subjects/<int:pk>/edit/', subject_update_view, name='admin_subject_edit'),
    path('admin-panel/subjects/<int:pk>/delete/', subject_delete_view, name='admin_subject_delete'),
]
