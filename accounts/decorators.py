from django.shortcuts import redirect


def role_required(*allowed_roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            # Allow Django superusers to access role-protected pages.
            if getattr(request.user, 'is_superuser', False):
                return view_func(request, *args, **kwargs)
            if request.user.role not in allowed_roles:
                return redirect('login')
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
