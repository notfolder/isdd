"""制服の貸与。物の登録、貸出、返却、履歴を扱う。"""

from app.modules.uniforms.routes import bp
from app.modules.uniforms.repo import SCHEMA

TITLE = "制服の貸与"

__all__ = ["bp", "TITLE", "SCHEMA"]
