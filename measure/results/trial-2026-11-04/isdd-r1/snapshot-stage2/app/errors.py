"""業務ルール違反を表す例外。"""


class RuleViolation(Exception):
    """業務ルールに違反したときに業務処理が送出する例外。

    message は利用者に出す文言。field を指定すると、その入力欄のエラーになる。
    level は画面の表示先で、"message"（操作の知らせ）か "error"（画面全体のエラー）。
    """

    def __init__(self, message: str, field: str | None = None, level: str = "message"):
        super().__init__(message)
        self.message = message
        self.field = field
        self.level = level
