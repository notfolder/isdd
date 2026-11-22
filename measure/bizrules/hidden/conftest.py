"""題材 bizrules の隠しテストの準備。お題 1 の準備処理（measure/hidden/conftest.py）と画面操作の補助をそのまま使う。"""

import importlib.util
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2] / "hidden"
sys.path.insert(0, str(BASE))
_spec = importlib.util.spec_from_file_location("base_conftest", BASE / "conftest.py")
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)

app = _base.app
new_page = _base.new_page
