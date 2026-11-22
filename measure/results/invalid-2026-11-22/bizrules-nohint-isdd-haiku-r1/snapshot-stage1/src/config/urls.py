"""URL と画面の割り当て。担当者以外の操作の拒否は 403 の画面で返す。"""
from django.shortcuts import render
from django.urls import path

from accounts import views as account_views
from equipment import views as equipment_views


def _permission_denied(request, exception=None):
    """権限が無い操作の 403 の画面を返す。"""
    return render(request, "403.html", status=403)


handler403 = "config.urls._permission_denied"

urlpatterns = [
    path("", equipment_views.status_view, name="status"),
    path("accounts/register/", account_views.register_view, name="register"),
    path("login/", account_views.login_view, name="login"),
    path("logout/", account_views.logout_view, name="logout"),
    path("equipment/new/", equipment_views.equipment_new_view, name="equipment_new"),
    path(
        "equipment/<str:equipment_number>/edit/",
        equipment_views.equipment_edit_view,
        name="equipment_edit",
    ),
    path(
        "equipment/<str:equipment_number>/delete/",
        equipment_views.equipment_delete_view,
        name="equipment_delete",
    ),
    path("lendings/new/", equipment_views.lending_new_view, name="lending_new"),
    path(
        "lendings/<str:equipment_number>/return/",
        equipment_views.lending_return_view,
        name="lending_return",
    ),
]
