"""アカウント登録・ログイン・ログアウトの画面処理。"""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm, RegisterForm
from .services import register_account

LOGIN_ERROR = "社員番号またはパスワードが違います"


def register_view(request):
    """アカウントを登録する。成功するとログイン画面へ移る。"""
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                register_account(
                    form.cleaned_data["employee_number"],
                    form.cleaned_data["name"],
                    form.cleaned_data["password"],
                )
            except IntegrityError:
                form.add_error("employee_number", "この社員番号は既に登録されています")
            else:
                messages.success(request, "登録しました。ログインしてください")
                return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    """社員番号とパスワードでログインする。失敗したら画面の .error に理由を出す。"""
    error = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            account = authenticate(
                request,
                username=form.cleaned_data["employee_number"],
                password=form.cleaned_data["password"],
            )
            if account is not None:
                login(request, account)
                return redirect("status")
            error = LOGIN_ERROR
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form, "error": error})


@require_POST
def logout_view(request):
    """ログアウトして貸出状況の画面へ移る。"""
    logout(request)
    return redirect("status")
