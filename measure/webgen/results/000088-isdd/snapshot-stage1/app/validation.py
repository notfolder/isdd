"""入力値の読み取りと検証。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Mapping, Optional

from app.constants import (
    AVERAGE_LENGTH_MAX_CM,
    CLASS_MAX_LENGTH,
    COMMON_NAME_MAX_LENGTH,
    CONSERVATION_STATUSES,
    DESCRIPTION_MAX_LENGTH,
    DIETS,
    HABITATS,
    KINGDOMS,
    SCIENTIFIC_NAME_MAX_LENGTH,
)

FIELD_NAMES: tuple[str, ...] = (
    "scientific_name",
    "common_name",
    "kingdom",
    "taxonomic_class",
    "habitat",
    "diet",
    "conservation_status",
    "average_length_cm",
    "description",
)

DUPLICATE_SCIENTIFIC_NAME_MESSAGE = "This scientific name is already registered."

_LENGTH_PATTERN = re.compile(r"^\d+(\.\d)?$")


@dataclass
class SpeciesForm:
    """登録・修正の入力値と、項目ごとのエラー。"""

    scientific_name: str = ""
    common_name: str = ""
    kingdom: str = ""
    taxonomic_class: str = ""
    habitat: str = ""
    diet: str = ""
    conservation_status: str = ""
    average_length_cm: str = ""
    description: str = ""
    errors: dict[str, str] = field(default_factory=dict)

    def field_values(self) -> dict[str, str]:
        """項目の入力値だけを辞書で返す（エラーは含めない）。"""
        return {name: getattr(self, name) for name in FIELD_NAMES}


def parse_species_form(data: Mapping[str, str]) -> SpeciesForm:
    """フォームの値を前後の空白を除いて SpeciesForm に写す。"""
    values = {name: data.get(name, "").strip() for name in FIELD_NAMES}
    return SpeciesForm(**values)


def validate_species_form(
    form: SpeciesForm,
    repository: Optional[object] = None,
    exclude_id: Optional[int] = None,
) -> None:
    """項目の規則と学名の一意性を確かめ、違反を form.errors に入れる。

    repository が渡されたときは、学名が他の種と重複しないかを確かめる。exclude_id は修正中の種の id。
    """
    errors: dict[str, str] = {}

    name = form.scientific_name
    if not 1 <= len(name) <= SCIENTIFIC_NAME_MAX_LENGTH:
        errors["scientific_name"] = "Scientific name is required and must be at most 100 characters."
    elif repository is not None and repository.find_id_by_scientific_name(name, exclude_id) is not None:
        errors["scientific_name"] = DUPLICATE_SCIENTIFIC_NAME_MESSAGE

    if not 1 <= len(form.common_name) <= COMMON_NAME_MAX_LENGTH:
        errors["common_name"] = "Common name is required and must be at most 100 characters."

    select_rules = (
        ("kingdom", KINGDOMS),
        ("habitat", HABITATS),
        ("diet", DIETS),
        ("conservation_status", tuple(CONSERVATION_STATUSES)),
    )
    for field_name, allowed in select_rules:
        if getattr(form, field_name) not in allowed:
            errors[field_name] = "Please select a value from the list."

    if len(form.taxonomic_class) > CLASS_MAX_LENGTH:
        errors["taxonomic_class"] = "Class must be at most 60 characters."

    if form.average_length_cm:
        match = _LENGTH_PATTERN.match(form.average_length_cm)
        if match is None:
            errors["average_length_cm"] = (
                "Average length must be a number greater than 0 and at most 100000, "
                "with at most one decimal place."
            )
        else:
            length = float(form.average_length_cm)
            if not 0 < length <= AVERAGE_LENGTH_MAX_CM:
                errors["average_length_cm"] = (
                    "Average length must be a number greater than 0 and at most 100000, "
                    "with at most one decimal place."
                )

    if len(form.description) > DESCRIPTION_MAX_LENGTH:
        errors["description"] = "Description must be at most 2000 characters."

    form.errors = errors
