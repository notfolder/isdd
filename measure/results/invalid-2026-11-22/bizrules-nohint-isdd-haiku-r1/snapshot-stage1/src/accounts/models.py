"""アカウント（社員）のモデル。社員番号でログインし、役割で担当者と社員を区別する。"""
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class Role(models.TextChoices):
    """アカウントの役割。担当者は備品と貸出を操作でき、社員は閲覧だけ。"""

    MANAGER = "M", "担当者"
    EMPLOYEE = "E", "社員"


class Account(AbstractBaseUser):
    """社員 1 人のアカウント。社員番号は一意。"""

    employee_number = models.CharField("社員番号", max_length=6, unique=True)
    name = models.CharField("名前", max_length=30)
    role = models.CharField("役割", max_length=1, choices=Role.choices)

    objects = BaseUserManager()

    USERNAME_FIELD = "employee_number"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        """借りる社員の選択肢に使う表示「名前（社員番号）」を返す。"""
        return f"{self.name}（{self.employee_number}）"
