import datetime

class HelloWorldPrinter:
    def get_current_time(self) -> str:
        return datetime.datetime.now().strftime("%H:%M:%S")

    def build_timestamped_message(self) -> str:
        time_str = self.get_current_time()
        return f"Hello, World! ({time_str})"

    def print_timestamped_output(self) -> None:
        message = self.build_timestamped_message()
        print(message)

if __name__ == "__main__":
    printer = HelloWorldPrinter()
    printer.print_timestamped_output()
