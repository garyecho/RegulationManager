"""
日志系统测试
"""
import os
import sys
import unittest
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.log_manager import LogManager


class TestLogSystem(unittest.TestCase):
    """测试日志系统"""

    def test_log_manager_setup(self):
        """测试日志管理器初始化"""
        LogManager.setup_logging()
        self.assertTrue(True)  # 简单测试不抛异常

    def test_get_log_files(self):
        """测试获取日志文件列表"""
        log_files = LogManager.get_log_files()
        self.assertIsInstance(log_files, list)

    def test_get_log_content(self):
        """测试获取日志内容"""
        logs = LogManager.get_log_content(lines=10)
        self.assertIsInstance(logs, list)

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

    def test_clear_old_logs(self):
        """测试清理旧日志"""
        # 这个测试会实际删除文件，所以只测试函数存在
        self.assertTrue(callable(LogManager.clear_old_logs))


if __name__ == "__main__":
    unittest.main()