import datetime
from typing import List, Dict


class LoggerManager:
    """
    システムログを一元管理するためのシングルトンクラス。
    全ての操作ログをメモリ上に記録し、後で履歴として参照できるようにする。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            # 初期化時に空のログリストを設定
            cls._instance._log_history: List[Dict] = []
        return cls._instance

    def log_event(self, event_type: str, details: str, message: str):
        """
        新しいイベントをログ履歴に追加する。

        Args:
            event_type (str): イベントの種別 ('UPPLOAD', 'ANALYZE_START', 'SUCCESS', 'ERROR'など)。
            details (str): 詳細な状況説明（例：処理したファイル名、対象カラム）。
            message (str): ユーザー向けの簡単なメッセージ。
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "details": details,
            "message": message,
        }
        self._log_history.append(log_entry)
        print(f"[LOG] {event_type}: {message}")  # コンソールにも出力する

    def get_history(self) -> List[Dict]:
        """
        記録されたすべてのログ履歴をリストとして取得する。
        """
        return self._log_history[:]


# グローバルなロガーインスタンスを提供するためのヘルパー関数 (シングルトンアクセスポイント)
def logger():
    return LoggerManager()
