"""Django の設定。データの置き場所、許可するホスト名、言語と時刻を環境変数から受け取る。"""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR") or BASE_DIR.parent / "data").resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _secret_key():
    """環境変数の秘密鍵を使う。無ければ DATA_DIR の secret_key を作って使う。"""
    env_key = os.environ.get("DJANGO_SECRET_KEY")
    if env_key:
        return env_key
    path = DATA_DIR / "secret_key"
    try:
        with open(path, "x", encoding="utf-8") as handle:
            handle.write(secrets.token_urlsafe(50))
        os.chmod(path, 0o600)
    except FileExistsError:
        pass
    return path.read_text(encoding="utf-8").strip()


SECRET_KEY = _secret_key()
DEBUG = False
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "accounts",
    "equipment",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "lending.sqlite3",
        # 書き込みのトランザクションを即時に開始し、同時の登録や貸出を直列化する
        "OPTIONS": {"transaction_mode": "IMMEDIATE"},
    },
}

AUTH_USER_MODEL = "accounts.Account"
# パスワードの強度検査は行わない（要件は 8 文字以上のみ）
AUTH_PASSWORD_VALIDATORS = []
LOGIN_URL = "login"

LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
