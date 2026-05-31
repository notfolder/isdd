# 要件ID: RQ-FT-PRINT-HELLO-WORLD
# 要件概要: Hello, World! 標準出力
# 設計ID: DS-MD-HELLO-MODULE-FT-PRINT-HELLO-WORLD
# 設計概要: CUI 実行エントリポイントおよび HelloWorldPrinter クラスの定義
# 呼び出し先設計ID: DS-FN-PRINT-HELLO-WORLD-FT-PRINT-HELLO-WORLD
# 呼び出し元設計ID: なし


# 要件ID: RQ-FT-PRINT-HELLO-WORLD
# 要件概要: Hello, World! 標準出力
# 設計ID: DS-CL-HELLO-WORLD-PRINTER-FT-PRINT-HELLO-WORLD
# 設計概要: 表示文字列の取得と標準出力表示を担当するクラス
# 呼び出し先設計ID: DS-FN-GET-HELLO-MESSAGE-FT-GET-HELLO-MESSAGE, DS-FN-PRINT-HELLO-WORLD-FT-PRINT-HELLO-WORLD
# 呼び出し元設計ID: DS-IF-CLI-ENTRY-FT-PRINT-HELLO-WORLD
class HelloWorldPrinter:
    # 要件ID: RQ-FT-GET-HELLO-MESSAGE
    # 要件概要: 表示文字列取得
    # 設計ID: DS-FN-GET-HELLO-MESSAGE-FT-GET-HELLO-MESSAGE
    # 設計概要: 固定文字列 "Hello, World!" を返す
    # 呼び出し先設計ID: なし
    # 呼び出し元設計ID: DS-FN-PRINT-HELLO-WORLD-FT-PRINT-HELLO-WORLD
    def get_hello_message(self) -> str:
        return "Hello, World!"

    # 要件ID: RQ-FT-PRINT-HELLO-WORLD
    # 要件概要: Hello, World! 標準出力
    # 設計ID: DS-FN-PRINT-HELLO-WORLD-FT-PRINT-HELLO-WORLD
    # 設計概要: get_hello_message の結果を標準出力へ表示する
    # 呼び出し先設計ID: DS-FN-GET-HELLO-MESSAGE-FT-GET-HELLO-MESSAGE
    # 呼び出し元設計ID: DS-IF-CLI-ENTRY-FT-PRINT-HELLO-WORLD
    def print_hello_world(self) -> None:
        message = self.get_hello_message()
        print(message)


# 要件ID: RQ-FT-PRINT-HELLO-WORLD
# 要件概要: Hello, World! 標準出力
# 設計ID: DS-IF-CLI-ENTRY-FT-PRINT-HELLO-WORLD
# 設計概要: エントリポイントとして HelloWorldPrinter を生成して print_hello_world を呼び出す
# 呼び出し先設計ID: DS-FN-PRINT-HELLO-WORLD-FT-PRINT-HELLO-WORLD
# 呼び出し元設計ID: なし
if __name__ == "__main__":
    printer = HelloWorldPrinter()
    printer.print_hello_world()
