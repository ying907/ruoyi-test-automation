import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BASE_URL = os.getenv("BASE_URL", "http://localhost").rstrip("/")
REDIS_CLI = os.getenv("REDIS_CLI", "")
LOGIN_USER = os.getenv("LOGIN_USER", "admin")
LOGIN_PASS = os.getenv("LOGIN_PASS", "")

EVIDENCE_DIR = Path(os.getenv("EVIDENCE_DIR", "screenshots"))
if not EVIDENCE_DIR.is_absolute():
    EVIDENCE_DIR = ROOT / EVIDENCE_DIR
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

BROWSERS = ["chrome", "msedge"]

if not REDIS_CLI:
    raise RuntimeError("缺少 REDIS_CLI：请在 .env 中配置 memurai-cli 路径")
if not LOGIN_PASS:
    raise RuntimeError("缺少 LOGIN_PASS：请在 .env 中配置登录密码")
