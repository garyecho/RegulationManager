"""
备份管理
"""
import zipfile
import logging
from datetime import datetime
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def create_backup(note: str = "") -> Path:
    """创建 ZIP 备份"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"backup_{ts}.zip"
    path = config.BACKUPS_DIR / name

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 备份数据库
        if config.DB_PATH.exists():
            zf.write(config.DB_PATH, "regulation.db")
        # 备份文档文件
        docs_dir = config.DOCUMENTS_DIR
        if docs_dir.exists():
            for f in docs_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f"documents/{f.relative_to(docs_dir)}")

    logger.info(f"备份已创建: {path}")
    return path


def restore_backup(zip_path: str) -> bool:
    """从 ZIP 恢复（拒绝 Zip Slip：成员路径必须落在 DATA_DIR 内）"""
    try:
        target_root = config.DATA_DIR.resolve()
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                name = info.filename
                if not name or name.endswith("/"):
                    continue
                dest = (config.DATA_DIR / name).resolve()
                # 拒绝绝对路径、盘符、以及 ../ 穿越到 DATA_DIR 之外
                if dest != target_root and target_root not in dest.parents:
                    logger.error(f"备份成员路径非法，已拒绝: {name}")
                    return False
            zf.extractall(config.DATA_DIR)
        logger.info(f"备份已恢复: {zip_path}")
        return True
    except Exception as e:
        logger.error(f"恢复失败: {e}")
        return False
