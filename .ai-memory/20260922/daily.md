
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

