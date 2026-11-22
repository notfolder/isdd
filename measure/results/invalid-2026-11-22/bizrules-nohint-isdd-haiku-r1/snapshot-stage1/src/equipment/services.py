"""備品の削除、貸出、返却の業務処理。どれも備品の行を取り直して状態を確かめてから書く。"""
from django.db import transaction

from .models import Equipment, Lending


class BusinessRuleError(Exception):
    """業務ルールに違反する操作。データは変えない。メッセージは画面にそのまま出す。"""


def _lock_equipment(equipment_pk):
    """備品の行を取り直す。無ければ業務エラーにする。"""
    equipment = Equipment.objects.select_for_update().filter(pk=equipment_pk).first()
    if equipment is None:
        raise BusinessRuleError("この備品は登録されていません")
    return equipment


def delete_equipment(equipment_pk):
    """空きの備品だけ削除する。貸出中なら業務エラーにする。"""
    with transaction.atomic():
        equipment = _lock_equipment(equipment_pk)
        if Lending.objects.filter(equipment=equipment).exists():
            raise BusinessRuleError("貸出中の備品は削除できません。先に返却してください")
        equipment.delete()


def lend_equipment(equipment_pk, borrower, lent_on):
    """空きの備品に貸出の記録を作る。貸出中なら業務エラーにする。"""
    with transaction.atomic():
        equipment = _lock_equipment(equipment_pk)
        if Lending.objects.filter(equipment=equipment).exists():
            raise BusinessRuleError("この備品は貸出中です")
        Lending.objects.create(equipment=equipment, borrower=borrower, lent_on=lent_on)


def return_equipment(equipment_pk):
    """貸出の記録を消して備品を空きに戻す。貸出中でなければ業務エラーにする。"""
    with transaction.atomic():
        equipment = _lock_equipment(equipment_pk)
        lending = Lending.objects.filter(equipment=equipment).first()
        if lending is None:
            raise BusinessRuleError("この備品は貸出中ではありません")
        lending.delete()
