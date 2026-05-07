class HelloWorldPrinter:
    def get_hello_message(self) -> str:
        return "Hello, World!"

    def print_hello_world(self) -> None:
        message = self.get_hello_message()
        print(message)


if __name__ == "__main__":
    printer = HelloWorldPrinter()
    printer.print_hello_world()
