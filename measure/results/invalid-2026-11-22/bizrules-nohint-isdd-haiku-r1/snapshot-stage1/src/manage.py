"""Django の管理コマンドの入口。"""
import os
import sys


def _main():
    """設定を読み込み、指定された管理コマンドを実行する。"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    _main()
