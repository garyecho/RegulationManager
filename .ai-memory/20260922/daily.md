
## [14:47] - 代码审查完成: 全项目只读审查（PyQt5+SQLite 制度管理系统）

- **文件**: 只读审查，未改业务代码；新建 `.ai-memory/20260922/daily.md`
- **决策**: 路由到 code-review；审计阶段只读不改码；发现 1 严重 / 3 警告 / 若干建议
- **验证**: `venv38\Scripts\python.exe -m unittest discover -s tests` → Ran 57 tests, OK；41 个 Python 文件 AST 解析 0 语法错误
## [15:05] - Bug修复完成: 修复审查5项

- **文件**: database/crud.py, core/scorecard_service.py, database/migrations.py, core/document_service.py, utils/text_utils.py, tests/test_document_service.py
- **决策**: FTS 用 app_meta.fts_schema_version 跳过无变重建; 标签 update 扣旧计新且同名去重; 引用超链一次加载 docs
- **验证**: venv38 unittest discover -s tests → Ran 59 tests OK


## [15:50] - Bug修复完成: 文号查重补全 + Zip Slip 防护

- **文件**: database/crud.py, utils/backup_manager.py, tests/test_document_service.py
- **决策**: check_duplicate 补 find_by_doc_no；restore_backup 解压前校验成员路径必须落在 DATA_DIR 内
- **验证**: venv38 unittest discover -s tests → Ran 60 tests OK


## [16:57] - 代码审查完成: 日志功能专项审查（log_manager/log_dialog/config/main）

- **文件**: 只读审查：utils/log_manager.py, ui/log_dialog.py, config.py, main.py, tests/test_log_system.py
- **决策**: 路由 code-review；审计只读不改码；发现 2 严重 / 3 警告 / 若干建议；推荐统一为单一 TimedRotating 或纯 Rotating + 收口 glob
- **验证**: 本地复现 RotatingFileHandler 产出 app_test.log.1（glob app_*.log 不匹配）；grep 证实 log_operation/log_user_action/log_performance 全库零调用

## [17:04] - Bug修复完成: 日志轮转漏扫 + 麒麟日志查看卡死

- **文件**: utils/log_manager.py, ui/log_dialog.py, config.py, main.py, tests/test_log_system.py
- **决策**: 改 TimedRotatingFileHandler(app.log 按天切分)；统一 app.log*/app_*.log* 收口；删除死代码 API；log_dialog 禁用 terminate，协作取消 + HTML 批量渲染 + 字体回退
- **验证**: venv38 unittest discover -s tests → Ran 63 tests OK；py_compile 5 文件通过
