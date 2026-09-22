"""
日志管理器 — 增强日志记录与查看功能
"""
import os
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import config

logger = logging.getLogger(__name__)


class LogManager:
    """日志管理器"""

    @staticmethod
    def setup_logging(level: int = logging.INFO, max_bytes: int = None, backup_count: int = None):
        """
        配置增强的日志系统
        
        Args:
            level: 日志级别
            max_bytes: 单个日志文件最大大小（默认从config读取）
            backup_count: 保留的备份日志文件数量（默认从config读取）
        """
        from logging.handlers import RotatingFileHandler
        
        # 使用配置文件中的默认值
        if max_bytes is None:
            max_bytes = config.LOG_MAX_BYTES
        if backup_count is None:
            backup_count = config.LOG_BACKUP_COUNT
        
        # 清除已有的 handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # 设置日志格式
        formatter = logging.Formatter(
            config.LOG_FORMAT,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器（轮转日志）
        file_handler = RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        
        # 配置根日志记录器
        root_logger.setLevel(level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        logger.info("日志系统已初始化，日志文件：%s", config.LOG_FILE)

    @staticmethod
    def get_log_files() -> List[Path]:
        """获取所有日志文件列表"""
        log_files = []
        if config.LOG_DIR.exists():
            for f in config.LOG_DIR.glob("app_*.log"):
                log_files.append(f)
            # 按修改时间排序，最新的在前
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return log_files

    @staticmethod
    def get_log_content(log_file: Optional[Path] = None, 
                        lines: int = 100, 
                        level_filter: Optional[str] = None,
                        keyword: Optional[str] = None) -> List[str]:
        """
        读取日志内容
        
        Args:
            log_file: 日志文件路径，默认为今天的日志
            lines: 读取的行数
            level_filter: 日志级别过滤（如 "ERROR", "WARNING"）
            keyword: 关键词过滤
            
        Returns:
            日志行列表
        """
        if log_file is None:
            log_file = config.LOG_FILE
        
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            # 过滤
            filtered_lines = []
            for line in all_lines:
                # 级别过滤
                if level_filter:
                    if f"[{level_filter}]" not in line:
                        continue
                
                # 关键词过滤
                if keyword:
                    if keyword.lower() not in line.lower():
                        continue
                
                filtered_lines.append(line.rstrip())
            
            # 返回最后N行
            return filtered_lines[-lines:] if len(filtered_lines) > lines else filtered_lines
            
        except Exception as e:
            logger.error("读取日志文件失败: %s", e)
            return []

    @staticmethod
    def get_error_logs(days: int = 7, lines: int = 50) -> List[str]:
        """获取最近几天的错误日志"""
        error_logs = []
        log_files = LogManager.get_log_files()
        
        # 过滤最近N天的日志
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_files = [
            f for f in log_files 
            if datetime.fromtimestamp(f.stat().st_mtime) >= cutoff_time
        ]
        
        for log_file in recent_files:
            errors = LogManager.get_log_content(
                log_file=log_file,
                level_filter="ERROR",
                lines=lines
            )
            error_logs.extend(errors)
        
        return error_logs[-lines:]

    @staticmethod
    def clear_old_logs(days: int = 30):
        """清理指定天数之前的旧日志文件"""
        if not config.LOG_DIR.exists():
            return 0
        
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for log_file in config.LOG_DIR.glob("app_*.log"):
            if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_time:
                try:
                    log_file.unlink()
                    deleted_count += 1
                    logger.info("已删除旧日志文件：%s", log_file.name)
                except Exception as e:
                    logger.error("删除日志文件失败：%s，错误：%s", log_file.name, e)
        
        return deleted_count

    @staticmethod
    def get_log_stats() -> Dict:
        """获取日志统计信息"""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "today_errors": 0,
            "today_warnings": 0,
        }
        
        if not config.LOG_DIR.exists():
            return stats
        
        log_files = list(config.LOG_DIR.glob("app_*.log"))
        stats["total_files"] = len(log_files)
        stats["total_size"] = sum(f.stat().st_size for f in log_files)
        
        # 今天的日志统计
        today_str = datetime.now().strftime("%Y%m%d")
        today_log = config.LOG_DIR / f"app_{today_str}.log"
        
        if today_log.exists():
            try:
                with open(today_log, 'r', encoding='utf-8') as f:
                    content = f.read()
                stats["today_errors"] = content.count("[ERROR]")
                stats["today_warnings"] = content.count("[WARNING]")
            except Exception:
                pass
        
        return stats

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


def log_operation(operation: str, details: str = "", level: int = logging.INFO):
    """
    记录用户操作的装饰器/函数
    
    Args:
        operation: 操作名称
        details: 操作详情
        level: 日志级别
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.log(level, "开始操作：%s %s", operation, details)
            try:
                result = func(*args, **kwargs)
                logger.log(level, "操作成功：%s", operation)
                return result
            except Exception as e:
                logger.error("操作失败：%s，错误：%s", operation, str(e), exc_info=True)
                raise
        return wrapper
    return decorator


def log_user_action(action: str, user: str = "default", details: str = ""):
    """记录用户操作日志"""
    logger.info("用户操作 [%s]: %s %s", user, action, details)


def log_performance(operation: str, duration: float, details: str = ""):
    """记录性能日志"""
    if duration > 1.0:  # 超过1秒的操作记录警告
        logger.warning("性能警告：%s 耗时 %.2f秒 %s", operation, duration, details)
    else:
        logger.debug("性能统计：%s 耗时 %.3f秒 %s", operation, duration, details)