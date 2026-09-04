"""
UI 样式 — 代码内联 QSS 所需的共享片段。

完整界面样式集中在 resources/styles/light.qss，
由各控件的 objectName 选择器统一接管，此处只保留走不了全局 QSS 的内联片段。
"""

# 通用中文字体族（代码内联 QSS 使用）
_FONT = ('"Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI Variable", '
         '"Segoe UI", "SimHei", "DengXian", sans-serif')
