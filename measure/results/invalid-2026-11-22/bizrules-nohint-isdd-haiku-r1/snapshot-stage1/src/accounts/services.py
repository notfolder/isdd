"""アカウント登録の業務処理。最初の登録者だけを担当者にする。"""
from django.db import transaction

from .models import Account, Role


def register_account(employee_number, name, password):
    """アカウントが 0 件なら担当者、1 件以上なら社員として登録する。

    判定と作成を 1 つのトランザクションで行い、同時の登録でも担当者は 1 人だけになるようにする。
    """
    with transaction.atomic():
        role = Role.EMPLOYEE if Account.objects.exists() else Role.MANAGER
        account = Account(employee_number=employee_number, name=name, role=role)
        account.set_password(password)
        account.save()
        return account
