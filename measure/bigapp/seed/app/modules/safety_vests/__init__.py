"""安全ベストの貸出。"""

from app.modules.safety_vests.models import SCHEMA
from app.modules.safety_vests.views import bp

TITLE = "安全ベストの貸出"

__all__ = ["bp", "TITLE", "SCHEMA"]
