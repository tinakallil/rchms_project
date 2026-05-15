                                                     
from functools import wraps
from django.core.exceptions import PermissionDenied
from .models import Role


def role_required(*allowed_roles):

       
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                raise PermissionDenied('Authentication required.')
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            profile = getattr(user, 'profile', None)
            if profile and profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied('Your role cannot access this page.')
        return _wrapped
    return decorator
