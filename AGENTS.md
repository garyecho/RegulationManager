# AGENTS.md — Regulation Manager

## Project Overview

Desktop app for managing company regulations (制度). PyQt5 + SQLAlchemy + SQLite. Python 3.8.10.
公司内部制度汇编管理系统。兼容 Windows 7–11（含 32/64 位），另有 Linux/Kylin 构建分支。

## Key Constraints

- **Python 3.8.10（Windows 打包）** — 不能使用 3.9+ 语法（如 `dict[int, int]`、`list[str]`），必须用 `typing.Dict`、`typing.List`、`typing.Tuple`。代码兼容 3.8–3.12；Ubuntu 开发环境用 Python 3.8.10（uv 托管，按 `.python-version` 自动安装，原因见 DEVELOPMENT.md）
- PyQt5（不是 PyQt6）

## Repos & Workflow

- 双 remote：`gitlab`（公司内网，`master` 的 upstream）+ `github`（https://github.com/garyecho/RegulationManager.git，私有镜像）
- 公司机器：`git push`（默认推 gitlab）；家里：`git push github master`
- 完整提交流程、双机同步、常见问题（如公司网络访问 GitHub 需代理）详见 **DEVELOPMENT.md**

## Quick Start

```bash
# Windows（公司）
cd D:\Code\RegulationManager
venv38\Scripts\python.exe main.py

# Linux（家里 Ubuntu，uv 管理）
uv sync
uv run python main.py
```

## Architecture

```
main.py                 → App entry, creates MainWindow
config.py               → All paths, constants, DB config (supports PyInstaller)
database/
  __init__.py            → Engine/session factory
  models.py             → 11 ORM tables（4 文档域 + 7 打分卡域）
  crud.py               → CRUD operations
  migrations.py         → DB init + FTS5 setup + path/text migration + 打分卡内置数据灌入
core/
  __init__.py
  document_service.py   → Document lifecycle (upload, search, delete, batch ops)
  category_service.py   → Category tree operations
  search_service.py     → FTS5 full-text search with LIKE fallback
  statistics_service.py → Stats aggregation
  scorecard_service.py  → 央行评级打分卡：树查询/编辑/制度关联/关键词搜索/引用自动识别超链
ui/
  __init__.py
  main_window.py        → Menu + toolbar + doc list + stats dashboard
  sidebar.py            → Category tree navigation
  document_panel.py     → Document list with pagination + batch selection
  add_edit_dialog.py    → Add/edit document form
  settings_dialog.py    → Settings (font size etc.)
  scorecard_panel.py    → 打分卡面板（左树钻取 + 右详情 + 搜索定位）
  scorecard_edit_dialog.py → 打分卡条目编辑 + 制度关联选择器
  components/
    __init__.py
    card_widget.py       → Card view widget
    tag_input.py         → Tag input widget
    toast.py             → Toast notification widget
  styles.py             → QSS style constants
utils/
  __init__.py
  search_engine.py      → FTS5 index management + jieba tokenization
  backup_manager.py     → ZIP backup/restore
  text_parser.py        → Title/doc_no extraction from filenames
  text_extractor.py     → Text extraction from doc/docx/pdf (no Windows-only deps)
  text_utils.py         → Misc text helpers
models/                 → Dataclass DTOs (DocumentData, CategoryData, SearchFilter, Scorecard* 等)
resources/
  styles/
    light.qss            → 浅色主题（唯一样式入口）
    dark.qss             → 深色主题（备用）
  rating/               → 打分卡内置初始数据（两份 JSON，首启灌库）
tests/                  → 单元测试（document_service, scorecard_service, citation_link）
tools/                  → 开发期一次性脚本（xls → 打分卡 JSON，不随应用分发）
```

## Data Flow

- Files stored in `data/documents/` with `{hash12}_{original_name}` naming
- SQLite DB at `data/regulation.db`
- FTS5 virtual table `documents_fts` for full-text search
- Relative paths stored in DB (relative to DATA_DIR), resolved at runtime
- `migrations.py` runs on every startup: rebuilds FTS5 index, migrates absolute paths, backfills missing content text, cleans obsolete categories, seeds 打分卡内置数据（幂等：仅首次），补 `is_auto` / `ignored_auto_ids` 列

## Key Conventions

- Chinese UI throughout (menus, labels, logs)
- File types: `.doc`, `.docx`, `.pdf` only
- Document dedup by file hash (SHA256)
- Soft delete → recycle bin (raw SQL), hard delete removes files
- Default categories seeded on first run (公司治理, 内部控制, 信用风险, etc.)
- Status auto-detection from filename/title keywords
- `data/`、`venv*`、`build/`、`dist/` are gitignored; runtime data never committed
- 样式集中在 `resources/styles/light.qss`，禁止 UI 类内 `widget.setStyleSheet()` 覆盖（动态样式除外）

## Database Schema

### 文档域（4 表）

| 表名 | 列数 | 说明 |
|------|------|------|
| `categories` | 7 | 分类树（id, name, parent_id, sort_order, icon, description, created_at） |
| `tags` | 5 | 标签（id, name, color, usage_count, created_at） |
| `documents` | 23 | 制度文档（title, doc_no, category_id, status, file_path, file_hash, content_text, is_deleted, …） |
| `document_tags` | 2 | 文档 ↔ 标签 M:N 关联（复合主键） |

### 打分卡域（7 表）

| 表名 | 列数 | 说明 |
|------|------|------|
| `scorecards` | 4 | 打分卡（按银行类型区分：城商农商民营 / 村镇银行） |
| `scorecard_modules` | 5 | 模块（如「一、公司治理」），UNIQUE(scorecard_id, name) |
| `scorecard_sections` | 5 | 一级指标（如「（一）组织架构」），UNIQUE(module_id, name) |
| `scorecard_items` | 5 | 二级指标（如「1.加强党的领导。」），UNIQUE(section_id, name) |
| `scorecard_checks` | 10 | 评级内容检查项（content, key_points, regulation_basis, review_materials, ignored_auto_ids） |
| `scorecard_check_documents` | 4 | 检查项 ↔ 制度文档 M:N 关联（is_auto 标记自动/手动关联） |

### FTS5

| 表名 | 说明 |
|------|------|
| `documents_fts` | 全文搜索虚拟表（title, doc_no, department, issuing_org, description, content_text） |

## Tests

| 测试文件 | 覆盖范围 |
|----------|----------|
| `tests/test_document_service.py` | 文档 CRUD、FTS5 索引、标签关联、批量操作 |
| `tests/test_scorecard_service.py` | 打分卡 seed 幂等、树结构、重名拒绝、关联替换、搜索命中 |
| `tests/test_citation_link.py` | 引用正则提取、文号归一化、匹配优先级、sync 持久化 |

## Incomplete Features

- 批量导出（Batch export）— 显示"开发中" toast
- 系统设置（System settings）— 部分实现：`settings_dialog.py` 已提供字体大小设置
