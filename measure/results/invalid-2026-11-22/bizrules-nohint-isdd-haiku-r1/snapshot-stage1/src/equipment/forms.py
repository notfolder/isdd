"""備品と貸出の入力検証。貸出日は今日（日本時間）以前に限る。"""
import re

from django import forms
from django.core.validators import MaxLengthValidator
from django.utils import timezone

from accounts.models import Account

from .models import Equipment

EQUIPMENT_NUMBER_PATTERN = re.compile(r"[A-Za-z0-9-]{1,20}")


def _validate_equipment_number(value):
    """管理番号は半角の英数字とハイフンで 20 文字以内。"""
    if not EQUIPMENT_NUMBER_PATTERN.fullmatch(value):
        raise forms.ValidationError("管理番号は半角の英数字とハイフンで 20 文字以内にしてください")


def _validate_lent_on(value):
    """貸出日は今日（日本時間）以前にする。"""
    if value > timezone.localdate():
        raise forms.ValidationError("貸出日は今日以前の日付にしてください")


class EquipmentForm(forms.ModelForm):
    """備品の登録と修正の入力。管理番号と備品名は前後の空白を除く。"""

    equipment_number = forms.CharField(
        label="管理番号",
        validators=[_validate_equipment_number],
    )
    name = forms.CharField(
        label="備品名",
        validators=[MaxLengthValidator(50)],
    )

    class Meta:
        model = Equipment
        fields = ["equipment_number", "name"]
        labels = {"name": "備品名"}


class LendingForm(forms.Form):
    """貸出の登録の入力。借りる社員は登録済みのアカウントから選ぶ。"""

    borrower = forms.ModelChoiceField(
        label="借りる社員",
        queryset=Account.objects.order_by("employee_number"),
    )
    lent_on = forms.DateField(
        label="貸出日",
        input_formats=["%Y-%m-%d"],
        validators=[_validate_lent_on],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
