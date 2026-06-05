# 制度汇编管理系统 v1.0.0

单机版制度文件集中管理系统，支持分类管理、全文搜索、标签管理、批量导入导出、回收站等功能。

## 功能特性

- **制度管理**：新增、编辑、删除（软删除+回收站）、彻底删除
- **分类目录**：树形分类、右键删除、底部添加、实时刷新
- **全文搜索**：基于 Whoosh + jieba 中文分词，支持标题、文号、部门、发文机关搜索
- **标签管理**：多标签关联、颜色标记、按标签筛选
- **批量操作**：批量导入文件夹、批量移入回收站、批量还原、批量彻底删除
- **智能解析**：自动提取文号（如"银保监规〔2022〕20号"）
- **统计看板**：制度总数、分类数量、状态分布等
- **数据备份**：一键备份/恢复，ZIP 格式

## 支持格式

| 格式 | 说明 |
|------|------|
| .doc | Word 97-2003 |
| .docx | Word 2007+ |
| .pdf | PDF 文档 |

## 目录结构

```
RegulationManager/
├── main.py                    # 程序入口
├── config.py                  # 全局配置
├── database/
│   ├── models.py              # SQLAlchemy ORM 模型
│   ├── crud.py                # CRUD 操作
│   └── migrations.py          # 数据库初始化 + FTS5
├── core/
│   ├── document_service.py    # 制度业务逻辑
│   ├── category_service.py    # 分类业务逻辑
│   ├── search_service.py      # 搜索服务
│   └── statistics_service.py  # 统计服务
├── ui/
│   ├── main_window.py         # 主窗口
│   ├── sidebar.py             # 左侧边栏（分类树）
│   ├── document_panel.py      # 文档列表面板
│   ├── add_edit_dialog.py     # 新增/编辑对话框
│   ├── styles.py              # 样式常量
│   └── components/
│       ├── toast.py           # Toast 提示
│       ├── card_widget.py     # 卡片组件
│       └── tag_input.py       # 标签输入框
├── models/
│   └── __init__.py            # DTO 数据传输对象
├── utils/
│   ├── text_parser.py         # 文号智能提取
│   ├── search_engine.py       # Whoosh 搜索引擎
│   └── backup_manager.py      # 备份管理
├── resources/
│   └── styles/
│       ├── dark.qss           # 深色主题
│       └── light.qss          # 亮色主题
└── data/
    ├── regulation.db          # SQLite 数据库
    ├── documents/             # 上传的制度文件
    ├── backups/               # 备份文件
    └── logs/                  # 运行日志
```

## 开发环境

### 依赖

```
PyQt6
sqlalchemy
whoosh
jieba
PyMuPDF (fitz)
python-docx
```

### 安装依赖

```bash
pip install PyQt6 sqlalchemy whoosh jieba PyMuPDF python-docx
```

### 运行

```bash
cd D:\Code\RegulationManager
python main.py
```

## 打包（PyInstaller）

### 一键打包

```bash
# 双击 build.bat 或在命令行执行：
pyinstaller RegulationManager.spec --clean --noconfirm
```

### 打包后结构

```
dist/RegulationManager/
├── RegulationManager.exe          # 主程序（双击运行）
├── _internal/                     # PyInstaller 运行时（勿删）
│   └── resources/styles/          # 样式文件
├── data/                          # 用户数据
│   ├── documents/                 # 制度文件
│   ├── backups/                   # 备份
│   └── logs/                      # 日志
├── README.txt                     # 使用说明
└── backup.txt                     # 备份说明
```

## 使用说明

### 添加制度

1. 点击工具栏「➕ 新增制度」或按 `Ctrl+N`
2. 选择文件、填写标题、文号、分类等信息
3. 点击保存

### 批量导入

1. 点击工具栏「📥 批量导入」
2. 选择包含制度文件的文件夹
3. 选择目标分类
4. 系统自动导入所有 .doc/.docx/.pdf 文件

### 分类管理

- **添加分类**：点击左侧底部「+ 添加分类」
- **删除分类**：右键分类项 → 删除（文档归入未分类）

### 搜索

- 在顶部搜索栏输入关键词，支持标题、文号、部门、发文机关搜索
- 按 `Enter` 或点击「搜索」按钮

### 备份与恢复

- **备份**：文件 → 备份制度库
- **恢复**：文件 → 恢复制度库 → 选择 .zip 备份文件

## 数据安全

所有数据存储在 `data/` 文件夹中：

| 文件 | 说明 |
|------|------|
| `regulation.db` | 数据库（制度信息、分类、标签） |
| `documents/` | 上传的制度文件 |
| `backups/` | 系统备份 |
| `logs/` | 运行日志 |

**重要提示**：

- 定期备份 `data/` 文件夹
- 不要删除 `regulation.db`，否则所有记录将丢失
- 不要删除 `documents/` 文件夹，否则制度文件将无法打开
- 迁移系统时，复制整个程序文件夹即可

## 技术栈

| 组件 | 技术 |
|------|------|
| GUI 框架 | PyQt6 |
| 数据库 | SQLite + SQLAlchemy |
| 全文搜索 | Whoosh + jieba |
| 文件解析 | PyMuPDF (PDF)、python-docx (Word) |
| 打包 | PyInstaller (onedir) |

## 常见问题

**Q: 双击 exe 无法启动？**
A: 确保路径中不含特殊字符，尝试以管理员身份运行。

**Q: 搜索不到内容？**
A: 首次导入文件后需要等待索引建立完成，大文件可能需要几秒。

**Q: 数据库损坏？**
A: 用备份文件替换 `data/regulation.db` 即可恢复。

**Q: 如何迁移数据？**
A: 复制整个程序文件夹（包含 `data/` 目录）到新位置即可。

## 版本历史

### v1.0.0 (2026-06)

- 初始版本
- 制度文件管理（新增、编辑、删除、回收站）
- 分类目录管理（树形结构、新增、删除）
- 全文搜索（Whoosh + jieba 中文分词）
- 标签管理
- 批量导入导出
- 统计看板
- 数据备份/恢复
- 深色/亮色主题
- 文号智能提取
