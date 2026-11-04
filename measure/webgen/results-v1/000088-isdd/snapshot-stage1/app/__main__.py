"""Web サーバーの起動。127.0.0.1 の PORT で前景に動かす。"""

import os

from app import create_app


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    application = create_app()
    application.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
