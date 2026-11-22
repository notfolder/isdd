"""貸出状況・備品・貸出の画面処理。操作は担当者だけに許し、貸出状況は誰でも見られる。"""
from django.contrib import messages
from django.utils import timezone
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import manager_required

from .forms import EquipmentForm, LendingForm
from .models import Equipment, Lending
from .services import (
    BusinessRuleError,
    delete_equipment,
    lend_equipment,
    return_equipment,
)


def status_view(request):
    """全備品の状態を管理番号の昇順で表示する。担当者にだけ操作ボタンを出す。"""
    equipment_list = Equipment.objects.select_related("lending__borrower").order_by(
        "equipment_number"
    )
    rows = [
        {"equipment": equipment, "lending": getattr(equipment, "lending", None)}
        for equipment in equipment_list
    ]
    can_operate = request.user.is_authenticated and request.user.role == "M"
    return render(
        request,
        "equipment/status.html",
        {"rows": rows, "can_operate": can_operate},
    )


@manager_required
def equipment_new_view(request):
    """備品を登録する。"""
    if request.method == "POST":
        form = EquipmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "備品を登録しました")
            return redirect("status")
    else:
        form = EquipmentForm()
    return render(request, "equipment/equipment_form.html", {"form": form})


@manager_required
def equipment_edit_view(request, equipment_number):
    """備品の管理番号と備品名を修正する。"""
    equipment = get_object_or_404(Equipment, equipment_number=equipment_number)
    if request.method == "POST":
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, "備品を修正しました")
            return redirect("status")
    else:
        form = EquipmentForm(instance=equipment)
    return render(
        request,
        "equipment/equipment_form.html",
        {"form": form, "editing": True, "current_number": equipment_number},
    )


@manager_required
@require_POST
def equipment_delete_view(request, equipment_number):
    """空きの備品を削除する。貸出中なら .error で理由を出し、削除しない。"""
    equipment = get_object_or_404(Equipment, equipment_number=equipment_number)
    try:
        delete_equipment(equipment.pk)
    except BusinessRuleError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "備品を削除しました")
    return redirect("status")


@manager_required
def lending_new_view(request):
    """空きの備品に貸出を登録する。貸出状況の画面の「貸出」から、管理番号を付けて開く。"""
    number = request.GET.get("equipment", "")
    if not number:
        raise Http404
    equipment = get_object_or_404(Equipment, equipment_number=number)
    is_lent = Lending.objects.filter(equipment=equipment).exists()
    if request.method == "POST":
        form = LendingForm(request.POST)
        if form.is_valid():
            try:
                lend_equipment(
                    equipment.pk,
                    form.cleaned_data["borrower"],
                    form.cleaned_data["lent_on"],
                )
            except BusinessRuleError as error:
                form.add_error(None, str(error))
            else:
                messages.success(request, "貸出を登録しました")
                return redirect("status")
    else:
        form = LendingForm(initial={"lent_on": timezone.localdate()})
    return render(
        request,
        "equipment/lending_form.html",
        {"form": form, "equipment": equipment, "is_lent": is_lent},
    )


@manager_required
@require_POST
def lending_return_view(request, equipment_number):
    """貸出の記録を消して備品を空きに戻す。"""
    equipment = get_object_or_404(Equipment, equipment_number=equipment_number)
    try:
        return_equipment(equipment.pk)
    except BusinessRuleError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "返却を記録しました")
    return redirect("status")
