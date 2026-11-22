"""起動の入口。設定を読み、データを用意し、業務層を組み立て、サーバーを起動する。

環境変数: PORT（待ち受けポート、既定 8000）、DATA_DIR（データの保存先、既定 ./data）。
"""

import os
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path

from waitress import serve

from data.database import Database
from data.repositories import EquipmentRepository, LendingRepository, UserRepository
from service.accounts import AccountService
from service.equipment import EquipmentService
from service.lending import LendingService
from web.app import create_app

DEFAULT_PORT = 8000
DEFAULT_DATA_DIR = "data"
DATABASE_FILE = "app.db"
SECRET_KEY_FILE = "secret_key"
LISTEN_HOST = "0.0.0.0"


@dataclass(frozen=True)
class Services:
    """画面に渡す業務層の入れ物。"""

    accounts: AccountService
    equipment: EquipmentService
    lending: LendingService


def build_services(data_dir: Path) -> Services:
    """データベースを開き（無ければ作り）、業務層を組み立てる。

    引数 data_dir: データの保存先のフォルダ。無ければ作る。
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    db = Database(data_dir / DATABASE_FILE)
    users = UserRepository()
    equipment_repo = EquipmentRepository()
    lending_repo = LendingRepository()
    return Services(
        accounts=AccountService(db, users),
        equipment=EquipmentService(db, equipment_repo, lending_repo),
        lending=LendingService(db, equipment_repo, lending_repo, users),
    )


def load_secret_key(data_dir: Path) -> str:
    """セッションの署名に使う秘密の値を返す。無ければ乱数で作り、権限 600 で保存する。"""
    path = data_dir / SECRET_KEY_FILE
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    key = secrets.token_hex(32)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(key)
    return key


def main() -> None:
    """設定を読み、アプリを組み立て、待ち受けを始める。"""
    data_dir = Path(os.environ.get("DATA_DIR") or DEFAULT_DATA_DIR).resolve()
    port = int(os.environ.get("PORT") or DEFAULT_PORT)
    services = build_services(data_dir)
    app = create_app(services, secret_key=load_secret_key(data_dir))
    print(f"備品の貸出管理を起動します: http://{LISTEN_HOST}:{port}/ (データ: {data_dir})",
          file=sys.stderr, flush=True)
    serve(app, host=LISTEN_HOST, port=port, threads=8)


if __name__ == "__main__":
    main()
