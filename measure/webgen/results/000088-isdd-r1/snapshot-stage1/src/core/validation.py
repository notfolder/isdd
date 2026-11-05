"""生物種の入力チェックと、一覧の検索条件の読み取り。

入力チェックは画面からの生の文字列を受け、整えた値とエラー文言の一覧を返す。
文言は利用者に英語で見せる。
"""

import math

from src.core.vocabulary import (
    CONSERVATION_STATUSES,
    DIETS,
    HABITATS,
    TAXONOMIC_CLASSES,
)

MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 1000
LIFESPAN_MIN = 1
LIFESPAN_MAX = 500
BODY_MASS_MAX = 200000.0

# 登録・修正フォームの項目名（画面の入力欄の name と同じ）
FORM_FIELDS = (
    "scientific_name",
    "common_name",
    "taxonomic_class",
    "habitat",
    "diet",
    "lifespan_years",
    "body_mass_kg",
    "conservation_status",
    "description",
)

# 選択欄の項目名、表示名、選択肢
CHOICE_FIELDS = (
    ("taxonomic_class", "Taxonomic class", TAXONOMIC_CLASSES),
    ("habitat", "Habitat", HABITATS),
    ("diet", "Diet", DIETS),
    ("conservation_status", "Conservation status", CONSERVATION_STATUSES),
)


def validate_species_input(values, is_name_taken):
    """登録・修正フォームの値を検査し、整えた値とエラー文言の一覧を返す。

    values は項目名から画面の生の文字列への辞書。is_name_taken は学名を受けて、
    別の生物種が同じ学名を使っているかを返す関数。
    戻り値は (整えた値の辞書, エラー文言のリスト)。エラーが無ければリストは空。
    """
    errors = []
    cleaned = {}

    scientific = values.get("scientific_name", "").strip()
    cleaned["scientific_name"] = scientific
    if not scientific:
        errors.append("Scientific name is required.")
    elif len(scientific) > MAX_NAME_LENGTH:
        errors.append("Scientific name must be 100 characters or fewer.")
    elif is_name_taken(scientific):
        errors.append("Scientific name already exists.")

    common = values.get("common_name", "").strip()
    cleaned["common_name"] = common
    if not common:
        errors.append("Common name is required.")
    elif len(common) > MAX_NAME_LENGTH:
        errors.append("Common name must be 100 characters or fewer.")

    for field, label, choices in CHOICE_FIELDS:
        value = values.get(field, "").strip()
        cleaned[field] = value
        if not value:
            errors.append(f"{label} is required.")
        elif value not in choices:
            errors.append(f"{label} must be one of the listed values.")

    cleaned["lifespan_years"], lifespan_error = _check_lifespan(values.get("lifespan_years", ""))
    if lifespan_error:
        errors.append(lifespan_error)

    cleaned["body_mass_kg"], mass_error = _check_body_mass(values.get("body_mass_kg", ""))
    if mass_error:
        errors.append(mass_error)

    description = values.get("description", "").strip()
    cleaned["description"] = description
    if len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append("Description must be 1000 characters or fewer.")

    return cleaned, errors


def _check_lifespan(raw):
    """寿命の入力を検査する。空欄は None。戻り値は (値, エラー文言または None)。"""
    text = raw.strip()
    if text == "":
        return None, None
    message = f"Lifespan must be a whole number from {LIFESPAN_MIN} to {LIFESPAN_MAX}."
    if not text.isdigit():
        return None, message
    number = int(text)
    if number < LIFESPAN_MIN or number > LIFESPAN_MAX:
        return None, message
    return number, None


def _check_body_mass(raw):
    """体重の入力を検査する。空欄は None。戻り値は (値, エラー文言または None)。"""
    text = raw.strip()
    if text == "":
        return None, None
    message = f"Body mass must be a number greater than 0 and at most {int(BODY_MASS_MAX)}."
    try:
        number = float(text)
    except ValueError:
        return None, message
    if not math.isfinite(number) or number <= 0 or number > BODY_MASS_MAX:
        return None, message
    return number, None


def read_filter_conditions(params):
    """一覧の検索条件を読み取る。

    params は項目名から文字列への辞書（クエリ文字列）。検索語は前後の空白を除く。
    選択欄の値は選択肢に含まれるものだけを採用し、それ以外は空（All）として扱う。
    戻り値は q と各選択欄の項目名を持つ辞書。
    """
    conditions = {"q": params.get("q", "").strip()}
    for field, _label, choices in CHOICE_FIELDS:
        value = params.get(field, "").strip()
        conditions[field] = value if value in choices else ""
    return conditions
