"""備品と貸出の単体・結合テスト。"""
import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from equipment.forms import EquipmentForm, LendingForm
from equipment.models import Equipment, Lending
from equipment.services import (
    BusinessRuleError,
    delete_equipment,
    lend_equipment,
    return_equipment,
)


@pytest.mark.parametrize("number", ["AB-1", "a" * 20, "PC0001"])
def test_equipment_number_accepts_valid_values(db, number):
    form = EquipmentForm({"equipment_number": number, "name": "備品"})
    assert form.is_valid(), form.errors


@pytest.mark.parametrize("number", ["a" * 21, "全角１", "ab_1", "", "AB 1"])
def test_equipment_number_rejects_invalid_values(db, number):
    form = EquipmentForm({"equipment_number": number, "name": "備品"})
    assert not form.is_valid()
    assert "equipment_number" in form.errors


def test_equipment_name_over_50_is_rejected(db):
    form = EquipmentForm({"equipment_number": "AB-1", "name": "あ" * 51})
    assert not form.is_valid()
    assert "name" in form.errors


def test_equipment_number_is_case_sensitive(db, make_equipment):
    make_equipment("AB-1")
    form = EquipmentForm({"equipment_number": "ab-1", "name": "備品"})
    assert form.is_valid(), form.errors


def test_delete_refuses_lent_equipment_and_keeps_data(db, make_account, make_equipment, lend):
    equipment = make_equipment("AB-1")
    lend(equipment, make_account("000001"), timezone.localdate())
    with pytest.raises(BusinessRuleError):
        delete_equipment(equipment.pk)
    assert Equipment.objects.filter(pk=equipment.pk).exists()


def test_delete_removes_available_equipment(db, make_equipment):
    equipment = make_equipment("AB-1")
    delete_equipment(equipment.pk)
    assert not Equipment.objects.filter(pk=equipment.pk).exists()


def test_lend_twice_is_refused_and_keeps_first_record(db, make_account, make_equipment):
    equipment = make_equipment("AB-1")
    first = make_account("000001")
    second = make_account("000002")
    today = timezone.localdate()
    lend_equipment(equipment.pk, first, today)
    with pytest.raises(BusinessRuleError):
        lend_equipment(equipment.pk, second, today)
    assert Lending.objects.get(equipment=equipment).borrower == first


def test_return_on_available_equipment_is_refused(db, make_equipment):
    equipment = make_equipment("AB-1")
    with pytest.raises(BusinessRuleError):
        return_equipment(equipment.pk)


def test_return_deletes_lending_record(db, make_account, make_equipment):
    equipment = make_equipment("AB-1")
    lend_equipment(equipment.pk, make_account("000001"), timezone.localdate())
    return_equipment(equipment.pk)
    assert not Lending.objects.filter(equipment=equipment).exists()


def test_lent_on_today_is_accepted_and_tomorrow_is_refused(db, make_account):
    borrower = make_account("000001")
    today = timezone.localdate()
    assert LendingForm({"borrower": borrower.pk, "lent_on": today.isoformat()}).is_valid()
    tomorrow = today + datetime.timedelta(days=1)
    form = LendingForm({"borrower": borrower.pk, "lent_on": tomorrow.isoformat()})
    assert not form.is_valid()
    assert "lent_on" in form.errors


def test_status_lists_in_ascending_order_for_guest(client, make_equipment):
    make_equipment("ZZ-9")
    make_equipment("AA-1")
    body = client.get(reverse("status")).content.decode()
    assert body.index('data-equipment-number="AA-1"') < body.index('data-equipment-number="ZZ-9"')
    assert "修正" not in body and "返却" not in body


def test_status_shows_empty_message_without_equipment(client, db):
    assert "備品は登録されていません" in client.get(reverse("status")).content.decode()


def test_guest_cannot_open_equipment_form(client, db):
    response = client.get(reverse("equipment_new"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


def test_employee_gets_403_on_equipment_form(client, make_account):
    account = make_account("000002", role=Role.EMPLOYEE)
    client.force_login(account)
    response = client.get(reverse("equipment_new"))
    assert response.status_code == 403
    assert "この操作は担当者だけができます" in response.content.decode()


def test_manager_sees_operation_buttons(client, make_account, make_equipment):
    manager = make_account("000001", role=Role.MANAGER)
    make_equipment("AB-1")
    client.force_login(manager)
    body = client.get(reverse("status")).content.decode()
    for label in ("修正", "削除", "貸出"):
        assert f">{label}</button>" in body
    assert "備品を登録" in body
