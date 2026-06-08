# 制度汇编管理系统 v1.0.2

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

## 系统要求

- **操作系统**：Windows 7 SP1 / 8 / 10 / 11（32位和64位均可）
- **运行环境**：无需安装 Python，解压即用
- **可选依赖**：如提示缺少 VCRUNTIME140.dll，请安装 [Visual C++ Redistributable 2015-2022](https://aka.ms/vs/17/release/vc_redist.x64.exe)

## 目录结构

```
RegulationManager/
├── main.py                    # 程序入口
├── config.py                  # 全局配置（兼容打包模式）
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
├── data/
│   ├── regulation.db          # SQLite 数据库
│   ├── documents/             # 上传的制度文件
│   ├── backups/               # 备份文件
│   └── logs/                  # 运行日志
├── RegulationManager.spec     # PyInstaller 打包配置（支持 BUILD_ARCH 环境变量）
├── build.bat                  # 一键双架构打包脚本
├── setup_x86.bat              # 32位环境搭建脚本（只需运行一次）
├── venv38/                    # 64位打包虚拟环境
├── venv38_x86/                # 32位打包虚拟环境
└── dist_files/
    ├── README.txt             # 用户使用说明（打包时复制到交付目录）
    └── backup.txt             # 备份说明
```

## 开发环境

### 依赖

```
PyQt5
sqlalchemy
whoosh
jieba
PyMuPDF (fitz)
python-docx
pyinstaller
```

### 安装依赖

```bash
pip install PyQt5 sqlalchemy whoosh jieba PyMuPDF python-docx pyinstaller
```

### 运行（开发模式）

```bash
cd D:\Code\RegulationManager
python main.py
```

## 打包（PyInstaller）

### 为什么用 Python 3.8 打包

- **Python 3.9+ 不支持 Windows 7**：会报 `api-ms-win-core-path-l1-1-0.dll` 缺失
- **Python 3.8 是最后一个支持 Windows 7 的版本**
- 打包后的 exe 内嵌了 Python 运行时，用 3.8 打包就能在 Win7~Win11 全系列运行

> Python 3.8 已于 2024 年 10 月 EOL，但仅用于打包不影响安全性。

### 打包步骤

#### 1. 安装 Python 3.8（64位 + 32位）

| 架构 | 下载地址 |
|------|---------|
| 64位 | https://www.python.org/downloads/release/python-3810/ → "Windows x86-64 executable installer" |
| 32位 | https://www.python.org/downloads/release/python-3810/ → "Windows x86 executable installer" |

安装时**不要勾选** "Add Python 3.8 to PATH"（避免覆盖默认的 Python）。

#### 2. 创建虚拟环境

```cmd
cd D:\Code\RegulationManager

# 64位虚拟环境
py -3.8 -m venv venv38

# 32位虚拟环境（需要先安装 Python 3.8 32位）
py -3.8-32 -m venv venv38_x86
```

也可以直接运行 `setup_x86.bat` 自动完成 32 位环境搭建。

#### 3. 安装依赖

分别在两个 venv 中安装：

```cmd
# 64位
call venv38\Scripts\activate
pip install PyQt5==5.15.11 sqlalchemy whoosh jieba PyMuPDF==1.24.11 python-docx pyinstaller -i http://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
deactivate

# 32位
call venv38_x86\Scripts\activate
pip install PyQt5==5.15.11 sqlalchemy whoosh jieba PyMuPDF==1.24.11 python-docx pyinstaller -i http://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
deactivate
```

#### 4. 打包

```cmd
# 同时打包 64位 + 32位
build.bat

# 只打 64位
build.bat x64

# 只打 32位
build.bat x86
```

### 打包后结构

```
dist/
├── RegulationManager_x64/         # 64位版本
│   ├── RegulationManager.exe      # 主程序
│   ├── _internal/                 # PyInstaller 运行时（勿删）
│   ├── data/                      # 用户数据
│   ├── README.txt
│   └── backup.txt
└── RegulationManager_x86/         # 32位版本（Win7 32位专用）
    ├── RegulationManager.exe
    ├── _internal/
    ├── data/
    ├── README.txt
    └── backup.txt
```

### 关于虚拟环境（venv）

```
系统 Python 3.13：    C:\...\Python313\python.exe       ← 日常开发用
64位 Python 3.8：     D:\...\venv38\Scripts\python.exe   ← 64位打包
32位 Python 3.8：     D:\...\venv38_x86\Scripts\python.exe ← 32位打包
```

- venv 是 Python 的独立副本，有自己的包目录（`venv38\Lib\site-packages\`）
- 两个 venv 完全隔离，互不影响
- 打包完成后可删除 `venv38` 和 `venv38_x86` 文件夹

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
| GUI 框架 | PyQt5 5.15（兼容 Win7~Win11） |
| 数据库 | SQLite + SQLAlchemy |
| 全文搜索 | Whoosh + jieba |
| 文件解析 | PyMuPDF (PDF)、python-docx (Word) |
| 打包 | PyInstaller 6.x (onedir) |
| 打包 Python | 3.8（兼容 Win7~Win11） |

## 常见问题

**Q: 双击 exe 无法启动？**
A: 确保路径中不含特殊字符，尝试以管理员身份运行。

**Q: Win7 提示缺少 VCRUNTIME140.dll？**
A: 安装 Visual C++ Redistributable 2015-2022 即可。

**Q: 搜索不到内容？**
A: 首次导入文件后需要等待索引建立完成，大文件可能需要几秒。

**Q: 数据库损坏？**
A: 用备份文件替换 `data/regulation.db` 即可恢复。

**Q: 如何迁移数据？**
A: 复制整个程序文件夹（包含 `data/` 目录）到新位置即可。

## 版本历史

### v1.0.2 (2026-06)

- **双架构打包**：`build.bat` 一键同时产出 x64 和 x86 版本
- **32位支持**：Win7 32位系统可运行 x86 版本
- 新增 `setup_x86.bat` 一键搭建 32 位打包环境
- `RegulationManager.spec` 支持 `BUILD_ARCH` 环境变量动态命名输出目录
- 代码重构：提取 FTS 触发器/时间戳/文件删除/批量操作等公共函数，消除重复代码
- 修复 `_current_sort` 未初始化导致的潜在 AttributeError
- 统计查询从 5 次单状态 COUNT 优化为 1 次 GROUP BY
- 清理所有未使用的导入（re/shutil/os/QEvent/QObject/QKeyEvent/QMenuBar 等）

### v1.0.1 (2026-06)

- **PyQt6 → PyQt5 迁移**：彻底解决 Windows 7 兼容性问题（Qt 6.0+ 不支持 Win7）
- 修复 `QFontDatabase.families()` 在 PyQt5 中需实例调用的问题
- `build.bat` 自动激活 venv38 虚拟环境，避免打包时漏掉第三方库
- 所有 scoped enum 改为 flat enum（如 `Qt.AlignmentFlag.AlignCenter` → `Qt.AlignCenter`）
- `QAction` 从 `QtGui` 移回 `QtWidgets`（PyQt5 位置）

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
- 兼容 Windows 7 / 8 / 10 / 11
