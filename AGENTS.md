# AGENTS.md — Regulation Manager

## Project Overview

Desktop app for managing company regulations (制度). PyQt5 + SQLAlchemy + SQLite. Python 3.8.10.
公司内部制度汇编管理系统。兼容 Windows 7–11（含 32/64 位），另有 Linux/Kylin 构建分支。

## Key Constraints

- **Python 3.8.10（Windows 打包）** — 不能使用 3.9+ 语法（如 `dict[int, int]`、`list[str]`），必须用 `typing.Dict`、`typing.List`、`typing.Tuple`。代码兼容 3.8–3.12；Ubuntu 开发环境用 Python 3.12（原因见 DEVELOPMENT.md）
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
  models.py             → 4 ORM tables (categories, tags, documents, document_tags)
  crud.py               → CRUD operations
  migrations.py         → DB init + FTS5 setup + path/text migration
core/
  document_service.py   → Document lifecycle (upload, search, delete, batch ops)
  category_service.py   → Category tree operations
  search_service.py     → FTS5 full-text search with LIKE fallback
  statistics_service.py → Stats aggregation
ui/
  main_window.py        → Menu + toolbar + doc list + stats dashboard
  sidebar.py            → Category tree navigation
  document_panel.py     → Document list with pagination + batch selection
  add_edit_dialog.py    → Add/edit document form
  settings_dialog.py    → Settings (font size etc.)
  components/           → Reusable widgets (toast, cards, tag input)
  styles.py             → QSS style constants
utils/
  search_engine.py      → FTS5 index management + jieba tokenization
  backup_manager.py     → ZIP backup/restore
  text_parser.py        → Title/doc_no extraction from filenames
  text_extractor.py     → Text extraction from doc/docx/pdf (no Windows-only deps)
  text_utils.py         → Misc text helpers
models/                 → Dataclass DTOs (DocumentData, CategoryData, SearchFilter, etc.)
```

## Data Flow

- Files stored in `data/documents/` with `{hash12}_{original_name}` naming
- SQLite DB at `data/regulation.db`
- FTS5 virtual table `documents_fts` for full-text search
- Relative paths stored in DB (relative to DATA_DIR), resolved at runtime
- `migrations.py` runs on every startup: rebuilds FTS5 index, migrates absolute paths, backfills missing content text, cleans obsolete categories

## Key Conventions

- Chinese UI throughout (menus, labels, logs)
- File types: `.doc`, `.docx`, `.pdf` only
- Document dedup by file hash (SHA256)
- Soft delete → recycle bin (raw SQL), hard delete removes files
- Default categories seeded on first run (公司治理, 内部控制, 信用风险, etc.)
- Status auto-detection from filename/title keywords
- `data/`、`venv*`、`build/`、`dist/` are gitignored; runtime data never committed

## Database Schema

4 ORM tables: `categories`, `tags`, `documents`, `document_tags`（没有 document_versions 表）
FTS5 table: `documents_fts`（独立模式，jieba 预分词后手动填充）

## Incomplete Features

These show "开发中" toast:
- Batch export（批量导出）
- Theme switching（部分实现：`resources/styles/dark.qss` 与 `MainWindow._toggle_theme` 已存在但未完善）
- System settings（部分实现：`settings_dialog.py` 已提供字体大小设置）
