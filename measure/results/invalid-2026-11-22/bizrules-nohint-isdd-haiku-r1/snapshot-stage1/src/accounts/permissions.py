"""担当者だけに許す操作の装飾子。未ログインはログイン画面へ、社員は 403 にする。"""
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import Role


def manager_required(view):
    """担当者でないと view を実行しない。"""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.role != Role.MANAGER:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper
