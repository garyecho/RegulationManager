"""
日志系统测试
"""
import os
import sys
import unittest
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.log_manager import LogManager
import config


class TestLogSystem(unittest.TestCase):
    """测试日志系统"""

    def test_log_manager_setup(self):
        """测试日志管理器初始化"""
        LogManager.setup_logging()
        self.assertTrue(config.LOG_FILE.exists() or config.LOG_DIR.exists())

    def test_get_log_files(self):
        """测试获取日志文件列表（含轮转备份）"""
        LogManager.setup_logging()
        # 人为写一条并触发文件存在
        import logging
        logging.getLogger("test_log").info("probe")
        for h in logging.getLogger().handlers:
            h.flush()

        log_files = LogManager.get_log_files()
        self.assertIsInstance(log_files, list)
        self.assertTrue(any(f.name.startswith("app.log") or f.name.startswith("app_")
                            for f in log_files))

    def test_get_log_content(self):
        """测试获取日志内容"""
        logs = LogManager.get_log_content(lines=10)
        self.assertIsInstance(logs, list)

    def test_get_log_content_keyword_and_level(self):
        """测试级别/关键词过滤"""
        sample = config.LOG_DIR / "app.log.testfilter"
        try:
            sample.write_text(
                "2026-01-01 00:00:00 [INFO] a: hello\n"
                "2026-01-01 00:00:01 [ERROR] a: boom\n"
                "2026-01-01 00:00:02 [WARNING] b: warn-keyword\n",
                encoding="utf-8",
            )
            errors = LogManager.get_log_content(log_file=sample, level_filter="ERROR")
            self.assertEqual(len(errors), 1)
            self.assertIn("[ERROR]", errors[0])

            hits = LogManager.get_log_content(log_file=sample, keyword="warn-keyword")
            self.assertEqual(len(hits), 1)
        finally:
            if sample.exists():
                sample.unlink()

    def test_get_log_content_cancelled(self):
        """测试协作取消"""
        sample = config.LOG_DIR / "app.log.testcancel"
        try:
            sample.write_text("line1\nline2\n", encoding="utf-8")
            logs = LogManager.get_log_content(log_file=sample, cancelled=lambda: True)
            self.assertEqual(logs, [])
        finally:
            if sample.exists():
                sample.unlink()

    def test_get_error_logs(self):
        """测试获取错误日志"""
        error_logs = LogManager.get_error_logs(days=1, lines=10)
        self.assertIsInstance(error_logs, list)

    def test_get_log_stats(self):
        """测试获取日志统计"""
        stats = LogManager.get_log_stats()
        self.assertIn("total_files", stats)
        self.assertIn("total_size", stats)
        self.assertIn("today_errors", stats)
        self.assertIn("today_warnings", stats)

    def test_format_size(self):
        """测试格式化文件大小"""
        self.assertEqual(LogManager.format_size(1024), "1.0 KB")
        self.assertEqual(LogManager.format_size(1048576), "1.0 MB")

    def test_clear_old_logs_skips_active(self):
        """清理旧日志：保留活动日志，删除过期备份"""
        LogManager.setup_logging()
        active = config.LOG_FILE
        if not active.exists():
            active.write_text("active\n", encoding="utf-8")

        old_backup = config.LOG_DIR / "app.log.2000-01-01"
        old_backup.write_text("old\n", encoding="utf-8")
        old_time = (datetime.now() - timedelta(days=90)).timestamp()
        os.utime(old_backup, (old_time, old_time))

        deleted = LogManager.clear_old_logs(30)
        self.assertGreaterEqual(deleted, 1)
        self.assertFalse(old_backup.exists())
        self.assertTrue(active.exists())

    def test_rotated_backup_discoverable(self):
        """轮转备份文件必须能被 get_log_files / clear_old_logs 扫到"""
        LogManager.setup_logging()
        backup = config.LOG_DIR / "app.log.2020-01-01"
        backup.write_text("rotated\n", encoding="utf-8")
        try:
            names = {f.name for f in LogManager.get_log_files()}
            self.assertIn("app.log.2020-01-01", names)

            old_time = (datetime.now() - timedelta(days=90)).timestamp()
            os.utime(backup, (old_time, old_time))
            LogManager.clear_old_logs(30)
            self.assertFalse(backup.exists())
        finally:
            if backup.exists():
                backup.unlink()


if __name__ == "__main__":
    unittest.main()
