import datetime


# 要件ID: RQ-FT-PRINT-TIMESTAMPED-OUTPUT
# 要件概要: 時刻付きメッセージ標準出力
# 設計ID: DS-MD-HELLO-MODULE-FT-PRINT-TIMESTAMPED-OUTPUT
# 設計概要: CUI 実行エントリポイントおよび HelloWorldPrinter クラスの定義
# 呼び出し先設計ID: DS-FN-PRINT-TIMESTAMPED-OUTPUT-FT-PRINT-TIMESTAMPED-OUTPUT
# 呼び出し元設計ID: なし


# 要件ID: RQ-FT-PRINT-TIMESTAMPED-OUTPUT
# 要件概要: 時刻付きメッセージ標準出力
# 設計ID: DS-CL-HELLO-WORLD-PRINTER-FT-PRINT-TIMESTAMPED-OUTPUT
# 設計概要: 時刻取得・メッセージ生成・標準出力表示を担当するクラス
# 呼び出し先設計ID: DS-FN-GET-CURRENT-TIME-FT-GET-CURRENT-TIME, DS-FN-BUILD-TIMESTAMPED-MESSAGE-FT-BUILD-TIMESTAMPED-MESSAGE, DS-FN-PRINT-TIMESTAMPED-OUTPUT-FT-PRINT-TIMESTAMPED-OUTPUT
# 呼び出し元設計ID: DS-IF-CLI-ENTRY-FT-PRINT-TIMESTAMPED-OUTPUT
class HelloWorldPrinter:
    # 要件ID: RQ-FT-GET-CURRENT-TIME
    # 要件概要: 実行時刻取得
    # 設計ID: DS-FN-GET-CURRENT-TIME-FT-GET-CURRENT-TIME
    # 設計概要: ローカル時刻を HH:MM:SS 形式で返す
    # 呼び出し先設計ID: なし
    # 呼び出し元設計ID: DS-FN-BUILD-TIMESTAMPED-MESSAGE-FT-BUILD-TIMESTAMPED-MESSAGE
    def get_current_time(self) -> str:
        return datetime.datetime.now().strftime("%H:%M:%S")

    # 要件ID: RQ-FT-BUILD-TIMESTAMPED-MESSAGE
    # 要件概要: 時刻付きメッセージ生成
    # 設計ID: DS-FN-BUILD-TIMESTAMPED-MESSAGE-FT-BUILD-TIMESTAMPED-MESSAGE
    # 設計概要: "Hello, World! (HH:MM:SS)" 形式のメッセージを生成する
    # 呼び出し先設計ID: DS-FN-GET-CURRENT-TIME-FT-GET-CURRENT-TIME
    # 呼び出し元設計ID: DS-FN-PRINT-TIMESTAMPED-OUTPUT-FT-PRINT-TIMESTAMPED-OUTPUT
    def build_timestamped_message(self) -> str:
        time_str = self.get_current_time()
        return f"Hello, World! ({time_str})"

    # 要件ID: RQ-FT-PRINT-TIMESTAMPED-OUTPUT
    # 要件概要: 時刻付きメッセージ標準出力
    # 設計ID: DS-FN-PRINT-TIMESTAMPED-OUTPUT-FT-PRINT-TIMESTAMPED-OUTPUT
    # 設計概要: build_timestamped_message の結果を標準出力へ表示する
    # 呼び出し先設計ID: DS-FN-BUILD-TIMESTAMPED-MESSAGE-FT-BUILD-TIMESTAMPED-MESSAGE
    # 呼び出し元設計ID: DS-IF-CLI-ENTRY-FT-PRINT-TIMESTAMPED-OUTPUT
    def print_timestamped_output(self) -> None:
        message = self.build_timestamped_message()
        print(message)


# 要件ID: RQ-FT-PRINT-TIMESTAMPED-OUTPUT
# 要件概要: 時刻付きメッセージ標準出力
# 設計ID: DS-IF-CLI-ENTRY-FT-PRINT-TIMESTAMPED-OUTPUT
# 設計概要: エントリポイントとして HelloWorldPrinter を生成して print_timestamped_output を呼び出す
# 呼び出し先設計ID: DS-FN-PRINT-TIMESTAMPED-OUTPUT-FT-PRINT-TIMESTAMPED-OUTPUT
# 呼び出し元設計ID: なし
if __name__ == "__main__":
    printer = HelloWorldPrinter()
    printer.print_timestamped_output()
