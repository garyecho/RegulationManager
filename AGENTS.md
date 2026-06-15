# AGENTS.md — Regulation Manager

## Project Overview

Desktop app for managing company regulations (制度). PyQt5 + SQLAlchemy + SQLite. Python 3.8.10.

## Key Constraints

- **Python 3.8.10** — 不能使用 3.9+ 语法（如 `dict[int, int]`、`list[str]`），必须用 `typing.Dict`、`typing.List`、`typing.Tuple`
- PyQt5（不是 PyQt6）

## Quick Start

```bash
# Run the app
cd /mnt/d/Code/RegulationManager
venv/Scripts/python.exe main.py

# Install dependencies (if needed)
uv sync
```

## Architecture

```
main.py                 → App entry, creates MainWindow
config.py               → All paths, constants, DB config (supports PyInstaller)
database/
  models.py             → 5 ORM tables (categories, tags, documents, document_tags, document_versions)
  crud.py               → CRUD operations
  migrations.py         → DB init + FTS5 setup + seed default categories
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
  components/           → Reusable widgets (toast, cards, tag input)
  styles.py             → QSS style constants
utils/
  search_engine.py      → FTS5 index management + jieba tokenization
  backup_manager.py     → ZIP backup/restore
  text_parser.py        → Title/doc_no extraction from filenames
  text_extractor.py     → Text extraction from doc/docx/pdf
models/                 → Dataclass DTOs (DocumentData, CategoryData, SearchFilter, etc.)
```

## Data Flow

- Files stored in `data/documents/` with `{hash12}_{original_name}` naming
- SQLite DB at `data/regulation.db`
- FTS5 virtual table `documents_fts` for full-text search
- Relative paths stored in DB (relative to DATA_DIR), resolved at runtime

## Key Conventions

- Chinese UI throughout (menus, labels, logs)
- File types: `.doc`, `.docx`, `.pdf` only
- Document dedup by file hash (SHA256)
- Soft delete → recycle bin (raw SQL), hard delete removes files
- Default categories seeded on first run (公司治理, 内部控制, 信用风险, etc.)
- Status auto-detection from filename/title keywords

## Database Schema

5 ORM tables: `categories`, `tags`, `documents`, `document_tags`, `document_versions` (unused)
FTS5 table: `documents_fts`

## Incomplete Features

These show "开发中" toast:
- Batch export
- Theme switching
- System settings
