"""段ごとに変わる規則（既存機能の変更を測るため）。採点側が MEASURE_STAGE で段を渡す。

段 1: 社員番号 6 桁、役割の名称は「担当者」。
段 2: 社員番号 7 桁に変更（登録の検査・文言、ログイン、一覧と選択肢の表示）。
段 3: 「担当者」を「管理者」に全画面で改称（ボタン、列、文言）。
段 1 のテストは、段 2 以降はこの設定で「変更後の規則」のテストになる（変更の取りこぼしを拾う）。
"""

import os

STAGE = int(os.environ.get("MEASURE_STAGE", "1"))
EMP_DIGITS = 6 if STAGE < 2 else 7
ROLE = "担当者" if STAGE < 3 else "管理者"


def emp(n: str) -> str:
    """社員番号。段の桁数に 0 埋めする（"1" → "000001" / "0000001"）"""
    return n.zfill(EMP_DIGITS)


EMP_FORMAT_MSG = f"社員番号は {EMP_DIGITS} 桁の数字で入力してください"
STAFF_ONLY = f"この操作は{ROLE}だけが行えます"
LAST_STAFF = f"{ROLE}が 1 人もいなくなるため、この操作はできません"
BTN_MAKE_STAFF = f"{ROLE}にする"
BTN_UNMAKE_STAFF = f"{ROLE}から外す"
OLD_ROLE = "担当者"
