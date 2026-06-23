"""
全局配置
"""
import sys
from pathlib import Path
from datetime import datetime

# ── 路径（兼容 PyInstaller 打包模式）──
if getattr(sys, 'frozen', False):
    # 打包模式：PyInstaller 6.x 把资源放在 _internal/ 子目录
    EXE_DIR = Path(sys.executable).parent
    INTERNAL_DIR = EXE_DIR / "_internal"
    # 如果 _internal 存在则使用它（PyInstaller 6.x onedir 模式）
    if INTERNAL_DIR.exists():
        APP_DIR = INTERNAL_DIR
    else:
        APP_DIR = EXE_DIR
    # data 目录始终在 exe 同级（方便用户访问和备份）
    DATA_DIR = EXE_DIR / "data"
else:
    # 开发模式：脚本所在目录
    APP_DIR = Path(__file__).parent
    DATA_DIR = APP_DIR / "data"

RESOURCES_DIR = APP_DIR / "resources"
DOCUMENTS_DIR = DATA_DIR / "documents"
BACKUPS_DIR = DATA_DIR / "backups"
LOG_DIR = DATA_DIR / "logs"

# 确保目录存在
for d in [DATA_DIR, DOCUMENTS_DIR, BACKUPS_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── 应用信息 ──
APP_NAME = "制度汇编管理系统"
APP_VERSION = "1.1.0"

# ── 数据库 ──
DB_PATH = DATA_DIR / "regulation.db"
DB_URL = f"sqlite:///{DB_PATH}"

# ── 日志 ──
LOG_FILE = LOG_DIR / f"app_{datetime.now():%Y%m%d}.log"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# ── 文件类型 ──
ALLOWED_EXTENSIONS = {".doc", ".docx", ".pdf"}

# ── 文档状态 ──
DOC_STATUS_LABELS = {
    "active": "现行有效",
    "archived": "已归档",
    "superseded": "已被替代",
    "expired": "已废止",
}

# ── 分页 ──
DEFAULT_PAGE_SIZE = 20
