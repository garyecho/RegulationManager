"""
日志查看对话框 — 查看和管理系统日志
"""
import html
from datetime import datetime
from typing import List

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QComboBox,
    QLineEdit, QGroupBox, QGridLayout, QMessageBox,
    QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QFontInfo, QTextCursor

from utils.log_manager import LogManager
import config


class LogLoadWorker(QThread):
    """后台加载日志的线程（协作式取消，禁止 terminate）"""
    finished = pyqtSignal(int, list)
    error = pyqtSignal(int, str)

    def __init__(self, req_id, log_file=None, lines=100,
                 level_filter=None, keyword=None):
        super().__init__()
        self._req_id = req_id
        self._cancelled = False
        self.log_file = log_file
        self.lines = lines
        self.level_filter = level_filter
        self.keyword = keyword

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            logs = LogManager.get_log_content(
                self.log_file, self.lines, self.level_filter, self.keyword,
                cancelled=lambda: self._cancelled or self.isInterruptionRequested(),
            )
            if self._cancelled or self.isInterruptionRequested():
                return
            self.finished.emit(self._req_id, logs)
        except Exception as e:
            if not self._cancelled:
                self.error.emit(self._req_id, str(e))


class LogDialog(QDialog):
    """日志查看对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统日志查看器")
        self.setMinimumSize(900, 650)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self._req_seq = 0
        self._active_workers = []
        self._setup_ui()
        self._load_initial_data()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 顶部工具栏
        toolbar = QHBoxLayout()

        file_label = QLabel("日志文件：")
        toolbar.addWidget(file_label)

        self._file_combo = QComboBox()
        self._file_combo.setMinimumWidth(280)
        self._file_combo.currentIndexChanged.connect(self._on_file_changed)
        toolbar.addWidget(self._file_combo)

        self._btn_refresh = QPushButton("刷新")
        self._btn_refresh.clicked.connect(self._refresh_logs)
        toolbar.addWidget(self._btn_refresh)

        toolbar.addStretch()

        self._btn_export = QPushButton("导出日志")
        self._btn_export.clicked.connect(self._export_logs)
        toolbar.addWidget(self._btn_export)

        self._btn_cleanup = QPushButton("清理旧日志")
        self._btn_cleanup.clicked.connect(self._cleanup_logs)
        toolbar.addWidget(self._btn_cleanup)

        layout.addLayout(toolbar)

        # 过滤区域
        filter_group = QGroupBox("日志过滤")
        filter_layout = QGridLayout(filter_group)

        filter_layout.addWidget(QLabel("日志级别："), 0, 0)
        self._level_combo = QComboBox()
        self._level_combo.addItems(["全部", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self._level_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._level_combo, 0, 1)

        filter_layout.addWidget(QLabel("关键词搜索："), 0, 2)
        self._keyword_input = QLineEdit()
        self._keyword_input.setPlaceholderText("输入关键词搜索日志...")
        self._keyword_input.returnPressed.connect(self._on_filter_changed)
        filter_layout.addWidget(self._keyword_input, 0, 3)

        self._btn_search = QPushButton("搜索")
        self._btn_search.clicked.connect(self._on_filter_changed)
        filter_layout.addWidget(self._btn_search, 0, 4)

        filter_layout.addWidget(QLabel("显示行数："), 1, 0)
        self._lines_combo = QComboBox()
        self._lines_combo.addItems(["50", "100", "200", "500", "1000"])
        self._lines_combo.setCurrentText("100")
        self._lines_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._lines_combo, 1, 1)

        layout.addWidget(filter_group)

        # 日志内容显示
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        mono = QFont("Consolas")
        if not QFontInfo(mono).exactMatch():
            mono = QFont("Noto Sans Mono CJK SC")
            if not QFontInfo(mono).exactMatch():
                mono = QFont("Courier New")
        mono.setStyleHint(QFont.Monospace)
        self._log_text.setFont(mono)
        self._log_text.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self._log_text, 1)

        # 底部状态栏
        status_layout = QHBoxLayout()
        self._status_label = QLabel("就绪")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        self._stats_label = QLabel("")
        status_layout.addWidget(self._stats_label)
        layout.addLayout(status_layout)

        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

    def _load_initial_data(self):
        self._load_log_files()
        self._load_log_stats()
        self._load_logs()

    def _load_log_files(self):
        self._file_combo.blockSignals(True)
        self._file_combo.clear()
        log_files = LogManager.get_log_files()

        for log_file in log_files:
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                display_text = f"{log_file.name} ({mtime.strftime('%Y-%m-%d %H:%M')})"
            except OSError:
                display_text = log_file.name
            self._file_combo.addItem(display_text, log_file)

        if not log_files:
            self._file_combo.addItem("无日志文件", None)

        self._file_combo.blockSignals(False)

    def _load_log_stats(self):
        stats = LogManager.get_log_stats()
        size_str = LogManager.format_size(stats["total_size"])

        stats_text = f"共 {stats['total_files']} 个日志文件，总大小 {size_str}"
        if stats["today_errors"] > 0 or stats["today_warnings"] > 0:
            stats_text += f"，今日错误 {stats['today_errors']}，警告 {stats['today_warnings']}"

        self._stats_label.setText(stats_text)

    def _load_logs(self):
        current_file = self._file_combo.currentData()

        level_filter = self._level_combo.currentText()
        if level_filter == "全部":
            level_filter = None

        keyword = self._keyword_input.text().strip() or None
        lines = int(self._lines_combo.currentText())

        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, 0)
        self._status_label.setText("正在加载日志...")

        # 协作取消旧任务，绝不 QThread.terminate()
        self._cancel_active_workers()

        self._req_seq += 1
        req_id = self._req_seq
        worker = LogLoadWorker(req_id, current_file, lines, level_filter, keyword)
        worker.finished.connect(self._on_logs_loaded)
        worker.error.connect(self._on_load_error)
        worker.finished.connect(lambda _rid, _logs, w=worker: self._reap_worker(w))
        worker.error.connect(lambda _rid, _msg, w=worker: self._reap_worker(w))
        self._active_workers.append(worker)
        worker.start()

    def _cancel_active_workers(self):
        for worker in self._active_workers:
            worker.cancel()
            worker.requestInterruption()

    def _reap_worker(self, worker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        worker.deleteLater()

    def _on_logs_loaded(self, req_id, logs):
        if req_id != self._req_seq:
            return

        self._progress_bar.setVisible(False)

        if not logs:
            self._log_text.setPlainText("没有找到匹配的日志记录。")
            self._status_label.setText("无匹配记录")
            return

        self._render_logs(logs)
        self._status_label.setText(f"已加载 {len(logs)} 行日志")

    def _render_logs(self, logs: List[str]):
        """一次性批量渲染，避免麒麟/低端机上逐行 setTextColor 卡死"""
        self._log_text.clear()
        parts = []
        for line in logs:
            if "[ERROR]" in line or "[CRITICAL]" in line:
                color = "#c62828"
            elif "[WARNING]" in line:
                color = "#b26a00"
            elif "[DEBUG]" in line:
                color = "#757575"
            else:
                color = "#000000"
            parts.append(
                f'<span style="color:{color}">{html.escape(line)}</span>'
            )
        self._log_text.setHtml("<br>".join(parts))
        self._log_text.moveCursor(QTextCursor.End)

    def _on_load_error(self, req_id, error_msg):
        if req_id != self._req_seq:
            return
        self._progress_bar.setVisible(False)
        self._status_label.setText(f"加载失败：{error_msg}")
        QMessageBox.critical(self, "错误", f"加载日志失败：{error_msg}")

    def _on_file_changed(self, index):
        self._load_logs()

    def _on_filter_changed(self):
        self._load_logs()

    def _refresh_logs(self):
        self._load_log_files()
        self._load_log_stats()
        self._load_logs()

    def _export_logs(self):
        current_file = self._file_combo.currentData()
        if not current_file:
            QMessageBox.warning(self, "警告", "没有可导出的日志文件。")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", str(config.LOG_DIR / "exported_log.txt"),
            "文本文件 (*.txt);;所有文件 (*)"
        )
        if not file_path:
            return

        try:
            log_content = self._log_text.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
            QMessageBox.information(self, "成功", f"日志已导出到：\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出日志失败：{e}")

    def _cleanup_logs(self):
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
        """关闭事件：协作取消后台线程，禁止 terminate()（麒麟上会卡死）"""
        self._cancel_active_workers()
        event.accept()
