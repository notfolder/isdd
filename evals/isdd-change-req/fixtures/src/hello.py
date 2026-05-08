class HelloWorldPrinter:
    """
    要件ID: RQ-FT-PRINT-HELLO-WORLD
    設計ID: DS-CL-HELLO-WORLD-PRINTER-FT-PRINT-HELLO-WORLD
    要件概要: Hello, World! を標準出力に表示する
    設計概要: 表示文字列の取得と標準出力表示を担うクラス
    呼び出し先設計ID: DS-FN-GET-HELLO-MESSAGE-FT-GET-HELLO-MESSAGE, DS-FN-PRINT-HELLO-WORLD-FT-PRINT-HELLO-WORLD
    呼び出し元設計ID: DS-IF-CLI-ENTRY-FT-PRINT-HELLO-WORLD
    """

    def get_hello_message(self) -> str:
        """
        要件ID: RQ-FT-GET-HELLO-MESSAGE
        設計ID: DS-FN-GET-HELLO-MESSAGE-FT-GET-HELLO-MESSAGE
        要件概要: 表示文字列 "Hello, World!" を取得する
        設計概要: 固定文字列 "Hello, World!" を返す
        呼び出し先設計ID: なし
        呼び出し元設計ID: DS-FN-PRINT-HELLO-WORLD-FT-PRINT-HELLO-WORLD
        """
        return "Hello, World!"

    def print_hello_world(self) -> None:
        """
        要件ID: RQ-FT-PRINT-HELLO-WORLD
        設計ID: DS-FN-PRINT-HELLO-WORLD-FT-PRINT-HELLO-WORLD
        要件概要: Hello, World! を標準出力に表示する
        設計概要: get_hello_message の結果を print で標準出力へ表示する
        呼び出し先設計ID: DS-FN-GET-HELLO-MESSAGE-FT-GET-HELLO-MESSAGE
        呼び出し元設計ID: DS-IF-CLI-ENTRY-FT-PRINT-HELLO-WORLD
        """
        message = self.get_hello_message()
        print(message)


if __name__ == "__main__":
    printer = HelloWorldPrinter()
    printer.print_hello_world()
