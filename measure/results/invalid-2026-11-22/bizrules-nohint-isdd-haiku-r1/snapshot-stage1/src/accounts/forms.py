"""登録とログインの入力検証。入力欄ごとのエラーは field-error として画面に出す。"""
import re

from django import forms
from django.core.validators import MaxLengthValidator

from .models import Account

EMPLOYEE_NUMBER_PATTERN = re.compile(r"[0-9]{6}")


def _validate_employee_number(value):
    """社員番号は数字 6 桁で、既に登録されていないことを確かめる。"""
    if not EMPLOYEE_NUMBER_PATTERN.fullmatch(value):
        raise forms.ValidationError("社員番号は数字 6 桁で入力してください")
    if Account.objects.filter(employee_number=value).exists():
        raise forms.ValidationError("この社員番号は既に登録されています")


class RegisterForm(forms.Form):
    """アカウント登録の入力。名前は前後の空白を除き、パスワードは空白を保つ。"""

    employee_number = forms.CharField(
        label="社員番号",
        validators=[_validate_employee_number],
    )
    name = forms.CharField(label="名前", validators=[MaxLengthValidator(30)])
    password = forms.CharField(
        label="パスワード",
        min_length=8,
        validators=[MaxLengthValidator(128)],
        strip=False,
        widget=forms.PasswordInput(render_value=False),
    )


class LoginForm(forms.Form):
    """ログインの入力。パスワードは空白を保つ。"""

    employee_number = forms.CharField(label="社員番号")
    password = forms.CharField(
        label="パスワード",
        strip=False,
        widget=forms.PasswordInput(render_value=False),
    )
