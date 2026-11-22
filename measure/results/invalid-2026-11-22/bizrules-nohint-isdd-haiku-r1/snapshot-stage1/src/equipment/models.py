"""備品と貸出の記録のモデル。備品の状態は貸出の記録の有無で決まる。"""
from django.conf import settings
from django.db import models


class Equipment(models.Model):
    """備品 1 件。管理番号は一意で、大文字と小文字を区別する。"""

    equipment_number = models.CharField(
        "管理番号",
        max_length=20,
        unique=True,
        error_messages={"unique": "この管理番号は既に登録されています"},
    )
    name = models.CharField("備品名", max_length=50)

    class Meta:
        ordering = ["equipment_number"]


class Lending(models.Model):
    """貸出の記録 1 件。1 つの備品に対して最大 1 件。返却すると消す。"""

    equipment = models.OneToOneField(
        Equipment,
        on_delete=models.PROTECT,
        related_name="lending",
        verbose_name="備品",
    )
    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="lendings",
        verbose_name="借りる社員",
    )
    lent_on = models.DateField("貸出日")
