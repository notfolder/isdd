"""Start the Polls web server on 127.0.0.1 using the PORT and DATA_DIR environment variables.

Run with: python -m app
"""

import os
from pathlib import Path

from . import create_app

PROJECT_DIR = Path(__file__).resolve().parent.parent


def main() -> None:
    """Read PORT (default 8000) and DATA_DIR (default ./data), then serve the site."""
    port = int(os.environ.get("PORT", "8000"))
    data_dir = Path(os.environ.get("DATA_DIR", PROJECT_DIR / "data"))
    app = create_app(data_dir)
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
