"""テストの共通部品。チェッカーを外からコマンドとして実行し、終了コードと出力を返す。"""

import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "shared" / "scripts"


def run_script(name: str, args: List[str], cwd: Optional[Path] = None, scripts_dir: Path = SCRIPTS) -> Tuple[int, str]:
    """scripts_dir/<name>（既定は shared/scripts）を実行し、(終了コード, 標準出力と標準エラー) を返す"""
    proc = subprocess.run(
        [sys.executable, str(scripts_dir / name), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def write(root: Path, rel: str, content: str) -> Path:
    """root/rel に、先頭の共通インデントを外した content を書く"""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
    return path


class TempDirMixin:
    """各テストに一時ディレクトリ self.tmp を用意する"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()
