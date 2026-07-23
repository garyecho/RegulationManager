# 制度汇编管理系统 v1.2.3

单机版制度文件集中管理工具，面向金融/企业合规部门，支持分类管理、全文搜索（含正文检索）、批量导入、回收站等功能。支持 Windows 和银河麒麟操作系统。

## 功能概览

| 功能 | 说明 |
|------|------|
| 制度管理 | 新增、编辑、删除（软删除+回收站）、彻底删除 |
| 分类目录 | 树形分类结构，右键删除，底部添加 |
| 全文搜索 | FTS5 + jieba 中文分词，支持标题/文号/正文内容搜索 |
| 搜索高亮 | 搜索结果中关键词黄色背景高亮，显示正文摘要片段 |
| 正文提取 | 上传时自动提取 PDF/DOCX/DOC 正文，存入数据库供全文搜索 |
| 文号识别 | 自动从文件名提取文号（支持 `——`、`-`、`—` 分隔符） |
| 废止识别 | 文件名含"已废止"/"废止"/"失效"时自动标记状态 |
| 批量操作 | 批量导入文件夹、批量删除/还原/彻底删除 |
| 列自定义 | 拖拽列头调整顺序，拖拽边框调整列宽，自动保存，重启恢复 |
| 编辑功能 | 列表每行带编辑按钮，支持修改分类/状态/标题等字段 |
| 统计看板 | 制度总数、分类数量、状态分布 |
| 数据备份 | 一键备份/恢复，ZIP 格式 |
| 界面设置 | 字体大小调节（10-18px），实时预览，设置持久化 |
| 样式管理 | 浅色现代企业级 UI，样式集中在 `light.qss` 统一管理 |
| 打包分发 | 支持 Windows x64/x86 + 银河麒麟 x86_64 多平台打包，数据使用相对路径，可直接分发 |

## 支持格式

| 格式 | 说明 |
|------|------|
| `.doc` | Word 97-2003（存储+正文提取+全文搜索） |
| `.docx` | Word 2007+（存储+正文提取+全文搜索） |
| `.pdf` | PDF 文档（存储+正文提取+全文搜索） |

## 目录结构

```
RegulationManager/
├── main.py                        # 程序入口
├── config.py                      # 全局配置（路径/数据库/常量）
│
├── database/                      # 数据层
│   ├── models.py                  # SQLAlchemy ORM 模型（Document/Category/Tag）
│   ├── crud.py                    # CRUD 操作（DocumentCRUD/CategoryCRUD/TagCRUD）
│   └── migrations.py              # 数据库初始化 + FTS5 索引 + 路径迁移 + 正文补提
│
├── core/                          # 业务逻辑层
│   ├── document_service.py        # 制度生命周期（上传/编辑/删除/搜索/备份）
│   ├── category_service.py        # 分类 CRUD
│   ├── search_service.py          # 搜索服务（FTS5 查询）
│   └── statistics_service.py      # 统计查询
│
├── models/                        # 数据传输对象
│   └── __init__.py                # DocumentData/SearchResult/CategoryData 等 DTO
│
├── utils/                         # 工具层（无状态函数）
│   ├── text_parser.py             # 文号智能提取 + 废止状态识别
│   ├── text_extractor.py          # PDF/DOCX 正文提取（PyMuPDF/python-docx）
│   ├── search_engine.py           # FTS5 搜索引擎 + jieba 分词
│   └── backup_manager.py          # ZIP 备份/恢复
│
├── ui/                            # 界面层（PyQt5）
│   ├── main_window.py             # 主窗口（菜单栏+工具栏+三栏布局）
│   ├── sidebar.py                 # 左侧边栏（导航+分类树）
│   ├── document_panel.py          # 文档列表面板（表格/卡片视图+分页）
│   ├── add_edit_dialog.py         # 新增/编辑对话框
│   ├── styles.py                  # 样式常量（色板/字号/字体）
│   └── components/
│       ├── card_widget.py         # 卡片视图组件
│       ├── tag_input.py           # 标签输入组件
│       └── toast.py               # Toast 提示组件
│
├── resources/
│   └── styles/
│       ├── light.qss              # 浅色主题（唯一样式入口）
│       └── dark.qss               # 深色主题（备用）
│
├── data/                          # 运行时数据（不入版本控制）
│   ├── regulation.db              # SQLite 数据库
│   ├── documents/                 # 导入的制度文件
│   ├── backups/                   # 备份文件
│   └── logs/                      # 运行日志
│
├── dist_files/                    # 打包交付文件
│   ├── README.txt                 # 用户使用说明
│   └── backup.txt                 # 备份说明
│
├── RegulationManager.spec         # PyInstaller 打包配置
├── build.bat                      # 一键双架构打包脚本
├── setup_x86.bat                  # 32位环境搭建脚本
├── pyproject.toml                 # Python 项目配置
└── .gitignore
```

## 架构设计

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   UI 层     │───▶│  Core 层    │───▶│  Utils 层   │───▶│ Database 层 │
│ PyQt5 界面  │    │ 业务逻辑    │    │ 无状态工具   │    │ SQLAlchemy  │
│ main_window │    │ document_   │    │ text_parser │    │ models.py   │
│ sidebar     │    │ service.py  │    │ search_     │    │ crud.py     │
│ document_   │    │ category_   │    │ engine.py   │    │ migrations  │
│ panel.py    │    │ service.py  │    │ text_       │    │             │
└─────────────┘    └─────────────┘    │ extractor   │    └─────────────┘
                                      └─────────────┘
```

- **UI 层**：纯界面展示，不直接访问数据库，通过 Core 层调用
- **Core 层**：业务逻辑，协调 Utils 和 Database
- **Utils 层**：无状态工具函数，独立可测试
- **Database 层**：ORM 模型 + CRUD 操作 + 数据库迁移

## 开发环境

### 1. 创建虚拟环境

```powershell
cd D:\Code\RegulationManager
python -m venv venv
.\venv\Scripts\activate
```

### 2. 安装依赖

```powershell
pip install PyQt5 SQLAlchemy PyMuPDF python-docx jieba -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

> PyQt5 支持 Python 3.5-3.11，不支持 3.12+。推荐 Python 3.8 或 3.10。

### 3. 启动

```powershell
python main.py
```

程序启动时自动：
- 创建 SQLite 数据库
- 建立 FTS5 全文搜索索引
- 迁移旧的绝对路径为相对路径
- 为已有文档补提正文内容

## 样式管理

所有样式集中在 `resources/styles/light.qss` 一个文件中管理。

**禁止**在各 UI 类中使用 `widget.setStyleSheet()` 覆盖全局样式（动态样式除外）。

调整样式时，在 QSS 中搜对应的 `#objectName` 选择器：

| 想改这个 | 搜索关键词 |
|---------|-----------|
| 侧边栏背景 | `#Sidebar` |
| 主窗口背景 | `QMainWindow` |
| 表格内容字号 | `QTableWidget` |
| 表头字号 | `QHeaderView::section` |
| 按钮颜色 | `QPushButton` |
| 输入框 | `QLineEdit` |
| 选中行 | `::item:selected` |
| 主色调 | 全局替换 `#0066CC` |

**色板**：Primary=#0066CC  Accent=#0078D4  Success=#28A745  Danger=#DC3545

## 数据存储

| 文件 | 说明 | 入版本控制 |
|------|------|-----------|
| `data/regulation.db` | SQLite 数据库（制度信息+FTS5索引） | ❌ |
| `data/documents/` | 导入的制度文件 | ❌ |
| `data/backups/` | 手动备份 | ❌ |
| `data/logs/` | 运行日志 | ❌ |

**路径设计**：
- 数据库中的文件路径存储为**相对路径**（相对于 `data/` 目录）
- 运行时自动解析为绝对路径
- 分发时 `data/` 文件夹和 exe 在同一目录即可正常使用

**重要提示**：
- 定期备份 `data/` 文件夹
- 不要删除 `regulation.db`，否则所有记录丢失
- 不要删除 `documents/` 文件夹，否则文件无法打开
- 迁移系统时，复制整个程序文件夹即可

## 打包部署

### Python 3.8 打包（兼容 Win7~Win11）

Python 3.9+ 不支持 Windows 7，必须用 Python 3.8 打包。

| 架构 | 下载 |
|------|------|
| 64位 | https://www.python.org/downloads/release/python-3810/ → Windows x86-64 |
| 32位 | https://www.python.org/downloads/release/python-3810/ → Windows x86 |

安装时**不要勾选** "Add Python 3.8 to PATH"。

### 打包命令

```cmd
:: 创建虚拟环境
py -3.8 -m venv venv38
call venv38\Scripts\activate
pip install PyQt5==5.15.11 sqlalchemy PyMuPDF==1.24.11 python-docx jieba pyinstaller -i http://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

:: 打包
build.bat          :: 同时打 x64 + x86
build.bat x64      :: 只打 64位
build.bat x86      :: 只打 32位
```

### 打包后结构

```
dist/
├── RegulationManager_x64/          # Windows 64位
│   ├── RegulationManager.exe
│   ├── _internal/
│   └── data/
├── RegulationManager_x86/          # Windows 32位
│   └── ...
└── RegulationManager_Kylin_x64/    # 银河麒麟 x86_64
    ├── RegulationManager          # Linux 可执行文件
    ├── Launch_RegulationManager.desktop   # 双击直接启动
    ├── Install_RegulationManager.desktop  # 图形化安装到开始菜单
    ├── start.sh                   # 启动脚本（终端兜底）
    ├── install.sh                 # 安装脚本（终端兜底）
    ├── _internal/
    └── data/
```

### 麒麟系统构建

```bash
# 方式一：Docker 容器构建（在 Windows 上即可完成）
build_docker.bat          # 自动构建并打包为 tar.gz

# 方式二：在麒麟机器上直接构建
chmod +x build_linux.sh && ./build_linux.sh
```

### 分发注意事项

1. **必须**把 `data/` 文件夹和 exe 一起分发
2. 数据库中的文件路径已存为相对路径，换电脑可直接使用
3. 接收者无需重新导入，直接运行即可查看所有制度

### 麒麟零基础用户使用

推荐分发容器内生成的 `.tar.gz` 压缩包，避免 Windows 压缩软件丢失 Linux 执行权限。用户解压后：

1. 双击 `Launch_RegulationManager.desktop` 直接试用；首次出现“允许启动”或“信任并启动”时选择允许。
2. 需要长期使用时，双击 `Install_RegulationManager.desktop`；银河麒麟会通过 `pkexec` 弹出图形化密码框，认证后自动安装到 `/opt/RegulationManager` 并创建开始菜单入口。
3. 安装脚本会将 `data/` 目录交给实际登录用户，确保普通用户可以写入数据库、日志、备份和导入文件。
4. 若系统策略禁止执行桌面启动器，用户可在文件夹空白处右键选择“在终端中打开”，执行 `./start.sh` 或 `./install.sh`。Linux 输入密码时不显示字符或星号属于正常现象。

两个启动器的数据位置不同，不能混用：

| 启动方式 | 适用场景 | 程序与数据位置 | 是否需要密码 |
|------|------|------|------|
| `Launch_RegulationManager.desktop` | 临时试用 | 当前解压目录及其 `data/` | 否 |
| `Install_RegulationManager.desktop` | 长期使用 | `/opt/RegulationManager/` 及其 `data/` | 首次安装需要 |

安装时会复制当前解压目录的全部数据到 `/opt/RegulationManager/data/`。安装后应统一从开始菜单启动；如果又双击原解压目录中的启动器，会打开另一套旧数据，并非数据丢失。

## 使用说明

### 添加制度
工具栏「➕ 新增制度」或 `Ctrl+N` → 选择文件 → 自动识别文号/废止状态 → 填写信息 → 保存

### 编辑制度
列表每行右侧「✏ 编辑」按钮 → 修改分类/状态/标题 → 保存

### 批量导入
工具栏「📥 批量导入」→ 选择文件夹 → 选择目标分类 → 自动导入

### 搜索
顶部搜索栏输入关键词，支持搜索标题、文号、部门、**文档正文内容**

### 分类管理
- 添加：左侧底部「+ 添加分类」
- 删除：右键分类项 → 删除（文档归入未分类）

### 备份恢复
- 备份：文件 → 备份制度库
- 恢复：文件 → 恢复制度库 → 选择 .zip 备份文件

## 技术栈

| 组件 | 技术 |
|------|------|
| GUI | PyQt5 5.15（兼容 Win7~Win11 / 麒麟 v10~v11） |
| 数据库 | SQLite + SQLAlchemy |
| 全文搜索 | SQLite FTS5 + jieba 中文分词 |
| 正文提取 | PyMuPDF (PDF)、python-docx (DOCX) |
| 打包 | PyInstaller 6.x (onedir) / Docker 容器构建 |
| 主题 | 浅色主题 QSS（集中管理） |
| 平台 | Windows (x64/x86)、银河麒麟 (x86_64) |

## 常见问题

**Q: 双击 exe 无法启动？**
确保路径不含特殊字符，尝试以管理员身份运行。

**Q: Win7 提示缺少 VCRUNTIME140.dll？**
安装 [Visual C++ Redistributable 2015-2022](https://aka.ms/vs/17/release/vc_redist.x64.exe)。

**Q: 搜索不到正文内容？**
首次启动会自动补提正文。新上传的文件自动提取。如仍有问题，菜单「工具 → 重建搜索索引」。

**Q: 数据库损坏？**
用 `data/backups/` 中的备份替换 `data/regulation.db`。或删除数据库重启（数据丢失）。

**Q: 改了 QSS 不生效？**
检查对应控件是否有 `widget.setStyleSheet()` 内联样式覆盖了 QSS。用 `setObjectName()` 替代。

**Q: pip 安装报 SSL/proxy 错误？**
用国内镜像：`pip install ... -i http://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn`

**Q: 麒麟系统安装后数据“丢失”了？**
直接启动器使用解压目录下的 `data/`，开始菜单程序使用 `/opt/RegulationManager/data/`，两者不会自动同步。安装后请统一从开始菜单启动。

**Q: 麒麟系统双击启动器没有反应或打开了文本编辑器？**
右键 `Launch_RegulationManager.desktop`，选择“允许启动”或“属性 → 权限 → 允许作为程序执行”。仍无法启动时，在当前文件夹右键选择“在终端中打开”，执行：`chmod +x start.sh && ./start.sh`

**Q: 麒麟系统无法使用中文输入法？**
确保系统已安装 fcitx 输入法框架，执行：`sudo apt install fcitx-frontend-qt5 -y`

## 版本历史

### v1.2.3 (2026-07)

- **新增**: 麒麟图形启动器 `Launch_RegulationManager.desktop`，零基础用户可双击直接启动
- **新增**: 麒麟图形安装器 `Install_RegulationManager.desktop`，使用 `pkexec` 弹出系统图形密码认证框
- **优化**: 启动和安装脚本在图形环境中使用 `zenity` 显示中文成功或错误提示
- **优化**: 安装器无图形授权工具时提供明确的终端兜底指引
- **文档**: 说明直接启动与开始菜单安装的数据保存位置和切换注意事项

### v1.2.2 (2026-07)

- **修复**: 编辑标题、文号、部门、发文机关或备注后，FTS5 全文索引未同步更新
- **修复**: 文档元数据和 FTS5 索引改为同一事务提交，索引更新失败时自动回滚编辑
- **修复**: 带标签制度永久删除时因外键约束失败，并可能提前删除物理文件
- **修复**: 永久删除同步清理标签关联、标签使用次数和 FTS5 索引，失败时整体回滚
- **修复**: 重复记录共用物理文件时可能误删文件，兼容绝对路径和相对路径别名
- **修复**: 银河麒麟安装到 `/opt/RegulationManager` 后，普通用户无法写入数据库、日志和备份
- **优化**: 麒麟安装器支持 `pkexec`/`sudo` 用户传递、含空格路径和非交互运行
- **测试**: 新增 9 项文档服务回归测试和 2 项 Linux root 安装集成测试

### v1.2.1 (2026-07)

- **新增**: 银河麒麟 v10 SP1 / v11 x86_64 平台支持（Docker 容器构建 + 一键安装）
- **新增**: 新增制度时重复文件检测，弹出确认框提示（与批量导入行为一致）
- **新增**: 表格列支持拖拽排序和拖拽边框调宽，列宽和顺序自动保存，重启恢复
- **修复**: 回收站恢复文档后 FTS5 索引丢失（`_reindex_document` 函数缺失）
- **修复**: 启动时 FTS5 索引被清空且不重建，导致重启后正文搜索失效
- **修复**: FTS5 搜索结果未过滤已删除文档，回收站文档可能出现在搜索结果中
- **修复**: 排序按钮「按名称」不生效，始终按更新时间排序
- **修复**: 批量删除/还原/永久删除时 FTS5 索引可能不一致（对未成功操作的文档也更新索引）
- **修复**: Toast 弹出提示组件只隐藏不销毁，长期运行内存泄漏
- **修复**: 搜索结果摘要末尾多余的省略号

### v1.2.0 (2026-06)

- **安全修复**: 命令注入漏洞（使用 QDesktopServices 替代 os.system）
- **安全修复**: FTS5 查询注入（清除搜索词中的引号和特殊字符）
- **安全修复**: LIKE 通配符转义（防止 `%` `_` 被当作通配符）
- **修复**: 系统设置字体大小实时预览不生效（activeWindow 返回对话框本身）
- **修复**: 重建索引线程无法取消（关闭对话框后线程继续运行）
- **修复**: 重建索引对话框重复弹出（dlg.exec() 被调用两次）
- **修复**: QSS 字体替换误伤 padding/margin（改用正则精确匹配 font-size）
- **优化**: 重建索引写入次数减半（INSERT 时直接分词）
- **优化**: 侧边栏版本号从 config 动态读取
- **优化**: 提取公共 `highlight_text()` 函数，消除代码重复
- **优化**: 静默异常添加 debug 日志，防止 FTS5 索引静默失步
- **优化**: 魔法数字 `100000` 常量化为 `MAX_CONTENT_INDEX_LEN`
- **优化**: 分类树缓存，避免每次选分类都查询数据库

### v1.1.0 (2026-06)

- .doc 文件全文搜索支持（UTF-16LE 解码提取正文）
- 搜索结果关键词黄色背景高亮
- 搜索结果正文摘要片段显示
- 系统设置：字体大小调节（10-18px），实时预览，设置持久化
- 双击标题列打开源文件
- 重建索引进度条
- 表格行高/列宽随字体大小自适应
- FTS5 索引优化（独立模式 + jieba 预分词）
- 代码精简和性能优化

### v1.0.2 (2026-06)

- 浅色主题 UI，样式集中在 `light.qss` 统一管理
- 编辑功能：列表每行编辑按钮，支持修改分类/状态
- 正文全文搜索：上传时提取 PDF/DOCX 正文，FTS5 索引
- 文号识别增强：支持 `——`、`-`、`—` 三种分隔符
- 废止状态自动识别
- 文件路径改为相对路径，支持打包分发
- 双架构打包（x64 + x86）

### v1.0.1 (2026-06)

- PyQt6 → PyQt5 迁移（Win7 兼容）
- build.bat 自动激活 venv

### v1.0.0 (2026-06)

- 初始版本
- 制度管理、分类目录、全文搜索、标签、批量导入、统计看板、备份恢复
