"""
日志管理器 — 配置、查询、清理应用日志
"""
import logging
from collections import deque
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import List, Dict, Optional, Callable

import config

logger = logging.getLogger(__name__)

# 当前活动日志文件名（固定名，由 TimedRotatingFileHandler 按天切分）
ACTIVE_LOG_NAME = "app.log"


class LogManager:
    """日志管理器"""

    @staticmethod
    def setup_logging(level: int = logging.INFO, backup_count: int = None):
        """
        配置日志系统：按天轮转，固定主文件 app.log。

        Args:
            level: 日志级别
            backup_count: 保留的历史文件天数（默认从 config 读取）
        """
        if backup_count is None:
            backup_count = config.LOG_BACKUP_COUNT

        config.LOG_DIR.mkdir(parents=True, exist_ok=True)

        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass

        formatter = logging.Formatter(
            config.LOG_FORMAT,
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 按天切分：app.log → app.log.2026-09-21 …
        file_handler = TimedRotatingFileHandler(
            config.LOG_FILE,
            when='midnight',
            interval=1,
            backupCount=backup_count,
            encoding='utf-8',
            utc=False,
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)

        root_logger.setLevel(level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # 压低三方库噪声，避免刷屏业务日志
        for noisy in ("sqlalchemy", "PyQt5", "matplotlib", "PIL"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

        logger.info("日志系统已初始化，日志文件：%s", config.LOG_FILE)

    @staticmethod
    def _iter_log_files() -> List[Path]:
        """收集所有日志文件（含轮转备份 app.log.N / app.log.YYYY-MM-DD，以及旧版 app_*.log）"""
        if not config.LOG_DIR.exists():
            return []

        files = []
        seen = set()
        for pattern in ("app.log*", "app_*.log*"):
            for f in config.LOG_DIR.glob(pattern):
                if not f.is_file():
                    continue
                key = f.resolve()
                if key in seen:
                    continue
                seen.add(key)
                files.append(f)

        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return files

    @staticmethod
    def get_log_files() -> List[Path]:
        """获取所有日志文件列表（最新在前）"""
        return LogManager._iter_log_files()

    @staticmethod
    def get_log_content(log_file: Optional[Path] = None,
                        lines: int = 100,
                        level_filter: Optional[str] = None,
                        keyword: Optional[str] = None,
                        cancelled: Optional[Callable[[], bool]] = None) -> List[str]:
        """
        读取日志内容（流式过滤，仅保留最后 N 行）

        Args:
            log_file: 日志文件路径，默认为当前活动日志
            lines: 返回的最大行数
            level_filter: 日志级别过滤（如 "ERROR", "WARNING"）
            keyword: 关键词过滤
            cancelled: 协作式取消回调，返回 True 时中止读取

        Returns:
            日志行列表
        """
        if log_file is None:
            log_file = config.LOG_FILE

        if not log_file.exists():
            return []

        if lines <= 0:
            return []

        try:
            kept = deque(maxlen=lines)
            level_tag = f"[{level_filter}]" if level_filter else None
            keyword_lower = keyword.lower() if keyword else None

            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if cancelled is not None and cancelled():
                        return []
                    if level_tag and level_tag not in line:
                        continue
                    if keyword_lower and keyword_lower not in line.lower():
                        continue
                    kept.append(line.rstrip('\r\n'))

            return list(kept)
        except Exception as e:
            logger.error("读取日志文件失败: %s", e)
            return []

    @staticmethod
    def get_error_logs(days: int = 7, lines: int = 50) -> List[str]:
        """获取最近几天的错误日志"""
        error_logs = deque(maxlen=lines)
        log_files = LogManager.get_log_files()
        cutoff_time = datetime.now() - timedelta(days=days)

        for log_file in log_files:
            try:
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_time:
                    continue
            except OSError:
                continue

            errors = LogManager.get_log_content(
                log_file=log_file,
                level_filter="ERROR",
                lines=lines
            )
            error_logs.extend(errors)

        return list(error_logs)

    @staticmethod
    def clear_old_logs(days: int = 30) -> int:
        """清理指定天数之前的旧日志文件（含轮转备份；保留当前活动日志）"""
        if not config.LOG_DIR.exists():
            return 0

        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0
        active = config.LOG_FILE.resolve()

        for log_file in LogManager._iter_log_files():
            try:
                if log_file.resolve() == active:
                    continue
                if datetime.fromtimestamp(log_file.stat().st_mtime) >= cutoff_time:
                    continue
                log_file.unlink()
                deleted_count += 1
                logger.info("已删除旧日志文件：%s", log_file.name)
            except Exception as e:
                logger.error("删除日志文件失败：%s，错误：%s", log_file.name, e)

        return deleted_count

    @staticmethod
    def get_log_stats() -> Dict:
        """获取日志统计信息（流式统计当前活动日志，避免整读大文件）"""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "today_errors": 0,
            "today_warnings": 0,
        }

        if not config.LOG_DIR.exists():
            return stats

        log_files = LogManager._iter_log_files()
        stats["total_files"] = len(log_files)
        stats["total_size"] = 0
        for f in log_files:
            try:
                stats["total_size"] += f.stat().st_size
            except OSError:
                continue

        active = config.LOG_FILE
        if active.exists():
            try:
                with open(active, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        if "[ERROR]" in line:
                            stats["today_errors"] += 1
                        if "[WARNING]" in line:
                            stats["today_warnings"] += 1
            except Exception:
                pass

        return stats

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
