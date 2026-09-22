"""
日志系统演示脚本
展示如何使用新增的日志功能
"""
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

from utils.log_manager import LogManager
import logging

def main():
    print("=== 制度汇编管理系统 - 日志系统演示 ===\n")
    
    # 1. 初始化日志系统
    print("1. 初始化日志系统...")
    LogManager.setup_logging()
    logger = logging.getLogger("demo")
    
    # 2. 记录各种级别的日志
    print("2. 记录各种级别的日志...")
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    logger.critical("这是一条严重错误信息")
    
    # 3. 模拟用户操作
    print("3. 模拟用户操作...")
    logger.info("用户登录系统")
    logger.info("用户查看文档列表")
    logger.info("用户上传文档：关于加强内部控制的通知")
    logger.info("用户搜索关键词：风险管理")
    logger.info("用户导出文档列表")
    
    # 4. 模拟批量操作
    print("4. 模拟批量操作...")
    logger.info("开始批量导入，文件数量：5，跳过重复：True")
    for i in range(1, 6):
        logger.info("处理文件 %d/5：文档%d.docx", i, i)
    logger.info("批量导入完成，成功：5，失败：0，跳过：0")
    
    # 5. 获取日志统计
    print("5. 获取日志统计...")
    stats = LogManager.get_log_stats()
    print(f"   日志文件数量：{stats['total_files']}")
    print(f"   日志总大小：{LogManager.format_size(stats['total_size'])}")
    print(f"   今日错误数：{stats['today_errors']}")
    print(f"   今日警告数：{stats['today_warnings']}")
    
    # 6. 获取日志文件列表
    print("6. 获取日志文件列表...")
    log_files = LogManager.get_log_files()
    print(f"   找到 {len(log_files)} 个日志文件")
    for i, log_file in enumerate(log_files[:3], 1):
        print(f"   {i}. {log_file.name}")
    
    # 7. 获取错误日志
    print("7. 获取错误日志...")
    error_logs = LogManager.get_error_logs(days=1, lines=5)
    print(f"   找到 {len(error_logs)} 条错误日志")
    for log in error_logs[:3]:
        print(f"   - {log[:80]}...")
    
    # 8. 演示日志过滤
    print("8. 演示日志过滤...")
    warning_logs = LogManager.get_log_content(level_filter="WARNING", lines=5)
    print(f"   找到 {len(warning_logs)} 条警告日志")
    
    # 9. 显示日志文件位置
    print("9. 日志文件位置...")
    print(f"   日志文件：{LogManager.get_log_files()[0] if LogManager.get_log_files() else '无'}")
    print(f"   日志目录：{APP_DIR / 'data' / 'logs'}")
    
    print("\n=== 演示完成 ===")
    print("\n提示：")
    print("1. 在应用程序中，可以通过菜单 '工具 → 查看系统日志' 查看日志")
    print("2. 日志文件位于 data/logs/ 目录下")
    print("3. 系统会自动进行日志轮转，单个文件最大10MB")
    print("4. 可以通过日志查看器导出和清理日志文件")

if __name__ == "__main__":
    main()