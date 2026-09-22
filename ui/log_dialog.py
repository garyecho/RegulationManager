"""
日志查看对话框 — 查看和管理系统日志
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTextEdit, QPushButton, QLabel, QComboBox,
    QLineEdit, QGroupBox, QGridLayout, QMessageBox,
    QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

from utils.log_manager import LogManager
import config


class LogLoadWorker(QThread):
    """后台加载日志的线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, log_file=None, lines=100, level_filter=None, keyword=None):
        super().__init__()
        self.log_file = log_file
        self.lines = lines
        self.level_filter = level_filter
        self.keyword = keyword
    
    def run(self):
        try:
            logs = LogManager.get_log_content(
                self.log_file, self.lines, self.level_filter, self.keyword
            )
            self.finished.emit(logs)
        except Exception as e:
            self.error.emit(str(e))


class LogDialog(QDialog):
    """日志查看对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统日志查看器")
        self.setMinimumSize(900, 650)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        self._current_worker = None
        self._setup_ui()
        self._load_initial_data()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        
        # 日志文件选择
        file_label = QLabel("日志文件：")
        toolbar.addWidget(file_label)
        
        self._file_combo = QComboBox()
        self._file_combo.setMinimumWidth(200)
        self._file_combo.currentIndexChanged.connect(self._on_file_changed)
        toolbar.addWidget(self._file_combo)
        
        # 刷新按钮
        self._btn_refresh = QPushButton("刷新")
        self._btn_refresh.clicked.connect(self._refresh_logs)
        toolbar.addWidget(self._btn_refresh)
        
        toolbar.addStretch()
        
        # 导出按钮
        self._btn_export = QPushButton("导出日志")
        self._btn_export.clicked.connect(self._export_logs)
        toolbar.addWidget(self._btn_export)
        
        # 清理按钮
        self._btn_cleanup = QPushButton("清理旧日志")
        self._btn_cleanup.clicked.connect(self._cleanup_logs)
        toolbar.addWidget(self._btn_cleanup)
        
        layout.addLayout(toolbar)
        
        # 过滤区域
        filter_group = QGroupBox("日志过滤")
        filter_layout = QGridLayout(filter_group)
        
        # 日志级别过滤
        level_label = QLabel("日志级别：")
        filter_layout.addWidget(level_label, 0, 0)
        
        self._level_combo = QComboBox()
        self._level_combo.addItems(["全部", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self._level_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._level_combo, 0, 1)
        
        # 关键词搜索
        keyword_label = QLabel("关键词搜索：")
        filter_layout.addWidget(keyword_label, 0, 2)
        
        self._keyword_input = QLineEdit()
        self._keyword_input.setPlaceholderText("输入关键词搜索日志...")
        self._keyword_input.returnPressed.connect(self._on_filter_changed)
        filter_layout.addWidget(self._keyword_input, 0, 3)
        
        # 搜索按钮
        self._btn_search = QPushButton("搜索")
        self._btn_search.clicked.connect(self._on_filter_changed)
        filter_layout.addWidget(self._btn_search, 0, 4)
        
        # 显示行数
        lines_label = QLabel("显示行数：")
        filter_layout.addWidget(lines_label, 1, 0)
        
        self._lines_combo = QComboBox()
        self._lines_combo.addItems(["50", "100", "200", "500", "1000"])
        self._lines_combo.setCurrentText("100")
        self._lines_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._lines_combo, 1, 1)
        
        layout.addWidget(filter_group)
        
        # 日志内容显示
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFont(QFont("Consolas", 10))
        self._log_text.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self._log_text, 1)
        
        # 底部状态栏
        status_layout = QHBoxLayout()
        
        self._status_label = QLabel("就绪")
        status_layout.addWidget(self._status_label)
        
        status_layout.addStretch()
        
        # 日志统计
        self._stats_label = QLabel("")
        status_layout.addWidget(self._stats_label)
        
        layout.addLayout(status_layout)
        
        # 加载进度条
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)
    
    def _load_initial_data(self):
        """加载初始数据"""
        # 加载日志文件列表
        self._load_log_files()
        
        # 加载日志统计
        self._load_log_stats()
        
        # 加载今天的日志
        self._load_logs()
    
    def _load_log_files(self):
        """加载日志文件列表"""
        self._file_combo.clear()
        log_files = LogManager.get_log_files()
        
        for log_file in log_files:
            # 显示文件名和修改时间
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            display_text = f"{log_file.name} ({mtime.strftime('%Y-%m-%d %H:%M')})"
            self._file_combo.addItem(display_text, log_file)
        
        if not log_files:
            self._file_combo.addItem("无日志文件", None)
    
    def _load_log_stats(self):
        """加载日志统计信息"""
        stats = LogManager.get_log_stats()
        size_str = LogManager.format_size(stats["total_size"])
        
        stats_text = f"共 {stats['total_files']} 个日志文件，总大小 {size_str}"
        if stats["today_errors"] > 0 or stats["today_warnings"] > 0:
            stats_text += f"，今日错误 {stats['today_errors']}，警告 {stats['today_warnings']}"
        
        self._stats_label.setText(stats_text)
    
    def _load_logs(self):
        """加载日志内容"""
        # 获取当前选择的日志文件
        current_file = self._file_combo.currentData()
        
        # 获取过滤条件
        level_filter = self._level_combo.currentText()
        if level_filter == "全部":
            level_filter = None
        
        keyword = self._keyword_input.text().strip()
        if not keyword:
            keyword = None
        
        lines = int(self._lines_combo.currentText())
        
        # 显示加载状态
        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, 0)  # 不确定进度
        self._status_label.setText("正在加载日志...")
        self._log_text.clear()
        
        # 停止之前的加载线程
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait()
        
        # 启动后台加载线程
        self._current_worker = LogLoadWorker(
            current_file, lines, level_filter, keyword
        )
        self._current_worker.finished.connect(self._on_logs_loaded)
        self._current_worker.error.connect(self._on_load_error)
        self._current_worker.start()
    
    def _on_logs_loaded(self, logs):
        """日志加载完成"""
        self._progress_bar.setVisible(False)
        
        if not logs:
            self._log_text.setPlainText("没有找到匹配的日志记录。")
            self._status_label.setText("无匹配记录")
            return
        
        # 高亮显示不同级别的日志
        self._log_text.clear()
        cursor = self._log_text.textCursor()
        
        for line in logs:
            # 根据日志级别设置颜色
            if "[ERROR]" in line or "[CRITICAL]" in line:
                self._log_text.setTextColor(Qt.red)
            elif "[WARNING]" in line:
                self._log_text.setTextColor(Qt.darkYellow)
            elif "[DEBUG]" in line:
                self._log_text.setTextColor(Qt.gray)
            else:
                self._log_text.setTextColor(Qt.black)
            
            cursor.insertText(line + "\n")
        
        # 滚动到底部
        self._log_text.moveCursor(QTextCursor.End)
        
        self._status_label.setText(f"已加载 {len(logs)} 行日志")
    
    def _on_load_error(self, error_msg):
        """日志加载失败"""
        self._progress_bar.setVisible(False)
        self._status_label.setText(f"加载失败：{error_msg}")
        QMessageBox.critical(self, "错误", f"加载日志失败：{error_msg}")
    
    def _on_file_changed(self, index):
        """日志文件选择改变"""
        self._load_logs()
    
    def _on_filter_changed(self):
        """过滤条件改变"""
        self._load_logs()
    
    def _refresh_logs(self):
        """刷新日志"""
        self._load_log_files()
        self._load_log_stats()
        self._load_logs()
    
    def _export_logs(self):
        """导出日志"""
        current_file = self._file_combo.currentData()
        if not current_file:
            QMessageBox.warning(self, "警告", "没有可导出的日志文件。")
            return
        
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", str(config.LOG_DIR / "exported_log.txt"),
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        try:
            # 获取当前显示的日志内容
            log_content = self._log_text.toPlainText()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            QMessageBox.information(self, "成功", f"日志已导出到：\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出日志失败：{e}")
    
    def _cleanup_logs(self):
        """清理旧日志"""
        reply = QMessageBox.question(
            self, "确认清理",
            "确定要清理30天前的旧日志文件吗？\n\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            deleted_count = LogManager.clear_old_logs(30)
            QMessageBox.information(
                self, "清理完成",
                f"已清理 {deleted_count} 个旧日志文件。"
            )
            self._load_log_files()
            self._load_log_stats()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清理日志失败：{e}")
    
    def closeEvent(self, event):
        """关闭事件"""
        # 停止后台线程
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait()
        event.accept()


# 导入 datetime（在文件顶部导入会导致循环导入问题）
from datetime import datetime