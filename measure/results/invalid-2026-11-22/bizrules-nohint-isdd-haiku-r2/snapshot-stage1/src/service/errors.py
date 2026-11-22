"""業務層の業務エラーを表す例外。"""

from typing import Optional


class ServiceError(Exception):
    """業務エラー。画面全体の文言（message）と、入力欄ごとの文言（field_errors）を運ぶ。"""

    def __init__(self, message: str = "", field_errors: Optional[dict[str, str]] = None) -> None:
        """エラーを作る。

        引数 message: 画面全体に出す文言（無ければ空文字）。
        引数 field_errors: 入力欄の名前から文言への対応。
        """
        super().__init__(message or "入力に誤りがあります")
        self.message = message
        self.field_errors: dict[str, str] = dict(field_errors or {})


class NotFoundError(Exception):
    """対象の備品や利用者が存在しないことを表す例外。画面では 404 にする。"""
