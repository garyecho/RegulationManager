# DEVELOPMENT.md — 开发环境与提交流程

本文件说明本项目在两台机器（公司 Windows + 家里 Ubuntu）上的开发环境搭建，
以及日常提交 / 推送代码的标准流程。

- 技术栈：PyQt5 + SQLAlchemy + SQLite
- 依赖（见 `pyproject.toml` / `uv.lock`）：PyQt5、SQLAlchemy、PyMuPDF、python-docx、jieba

## 如何启动（速查）

| 平台 | 首次准备 | 启动命令 |
|---|---|---|
| Linux（家里 Ubuntu） | 装 uv → `uv sync` → `sudo apt install antiword fonts-noto-cjk` | `uv run python main.py` |
| Windows（公司，环境已配好） | 无需（依赖在 `venv38` 内） | `venv38\Scripts\python.exe main.py` |

首次启动会自动完成：创建 `data/`（`documents/`、`backups/`、`logs/`）→ 建库 `data/regulation.db`（4 张表）→ 重建 FTS5 全文索引（jieba 分词），全程无需手工初始化。

## 双远程仓库

| remote | 地址 | 用途 |
|---|---|---|
| `gitlab` | 公司内网 GitLab（`git remote -v` 查看） | 日常开发主仓库（master 的 upstream） |
| `github` | https://github.com/garyecho/RegulationManager.git | 私有镜像备份，家里开发时使用 |

> ⚠️ 公司内网 GitLab 只有公司网络（或 VPN）能访问；家里连不上。

## Python 版本策略

| 机器 | Python | 原因 |
|---|---|---|
| 公司 Windows | 3.8（`venv38` / `venv38_x86`） | 打包 Win7 兼容版 exe 的硬约束 |
| 家里 Ubuntu | 3.8.10（uv 托管，按 `.python-version` 自动安装/复用） | 与公司 Windows 打包解释器一致；Ubuntu 自带 3.13 无 PyQt5 5.15 wheel，故不用系统 Python |

代码使用 `typing` 兼容写法（`Dict` / `List`），在 3.8 ~ 3.12 均可运行。
**不要**在代码里使用 3.9+ 语法（如 `dict[int, int]`），否则公司 3.8 环境会报错。

## 一、Linux（家里 Ubuntu）——首次启动

```bash
# 1. 安装 uv（Python 解释器 + 依赖管理）
curl -LsSf https://astral.sh/uv/install.sh | sh
# 重开终端或 source ~/.bashrc 后生效

# 2. 克隆仓库（家里走 GitHub）
git clone https://github.com/garyecho/RegulationManager.git
cd RegulationManager

# 3. 安装依赖
#    自动读取 .python-version（3.8.10）；本机缺该解释器时 uv 会先自动下载，无需手动装 Python
uv sync

# 4. 系统依赖（一次性）：
#    antiword        提取老版 .doc 正文（可选，但装了 .doc 提取效果才好）
#    fonts-noto-cjk  中文字体，避免界面/文档中文显示为方块
sudo apt install antiword fonts-noto-cjk

# 5. 启动（日常启动也只跑这一条）
uv run python main.py
```

首次启动自动完成：创建 `data/documents`、`data/backups`、`data/logs` → 建库 `data/regulation.db` → 重建 FTS5 搜索索引（jieba 分词）。

跑通自检：① 窗口正常打开（标题"制度汇编管理系统"）；② 能添加分类；③ 导入 .pdf/.docx 后出现在列表、搜索能命中；④ 装过 antiword 时，老 .doc 也能提取出正文。

> 说明：`uv sync` = 创建项目内 `.venv/` + 按 `pyproject.toml` / `uv.lock` 安装依赖；本项目是平铺桌面应用（`python main.py` 启动），`pyproject.toml` 已设 `[tool.uv] package = false`，不会把自己构建成包。依赖有变动（改了 pyproject）时重跑 `uv sync` 即可；之后日常启动永远只需 `uv run python main.py`。

## 二、公司 Windows 环境

Windows 开发机不用 uv：依赖已装在虚拟环境里，沿用即可（`venv38` 64 位 / `venv38_x86` 32 位，见 `setup_x86.bat`）。

```bash
venv38\Scripts\python.exe main.py
```

首次启动同样自动创建 `data/` 并建库、重建搜索索引，无需手工初始化。

## 三、日常提交与推送

### 标准流程（两台机器通用）

```bash
git status                     # 1. 查看改动
git add .                      # 2. 暂存（data/、venv* 已被 .gitignore 拦截）
git commit -m "feat: 新增xxx功能"   # 3. 提交
```

### 推送（关键区别，取决于在哪台机器）

```bash
git push                       # 公司：upstream 是 gitlab，直接推内网
git push origin master         # 家里：内网连不上，推 GitHub
```

### 换机器同步

```bash
# 在家改完 → 回公司
git pull github master         # 公司机器上：拉取家里的改动
git push                       # 再同步到内网 gitlab

# 公司改完 → 回家
git pull github master         # 家里机器上：拉取公司同步的改动
```

### 提交信息规范

沿用项目现有风格（中文 + 类型前缀，参考 `git log`）：

- `feat: 新增批量导出`
- `fix: 修复搜索乱码`
- `docs: 更新README`
- `chore: 发布v1.2.3`
- `build(linux): 更新构建脚本`

## 四、常见问题

| 现象 | 处理 |
|---|---|
| 家里 `git push` / `git pull` 超时 | 默认 upstream 是 `gitlab`（内网），家里必须显式写 `github`：`git push github master` / `git pull github master`；或连公司 VPN 后直接推 gitlab |
| 启动报 `Could not find the Qt platform plugin "xcb" in ""` | `main.py` 已内置修复：启动时把 PyQt5 wheel 自带的插件目录加入 Qt 搜索路径（uv 托管 Python 下默认搜不到）。若换新机器仍报错，多半缺 Qt 运行库：`sudo apt install libxcb-cursor0 libxcb-xinerama0 libxkbcommon-x11-0 libegl1` 后重试 |
| Wayland 会话下启动直接段错误（退出码 139，无报错信息） | Qt5 在 Wayland 下默认走 xcb/XWayland，部分机器会崩。`main.py` 已自动处理：检测到 `XDG_SESSION_TYPE=wayland` 且未手动指定平台时，自动切 `QT_QPA_PLATFORM=wayland`。仍异常可手动：`QT_QPA_PLATFORM=wayland uv run python main.py` |
| `uv sync` 报 hatchling `Unable to determine which files to ship` | 旧问题：项目被当包构建失败。`pyproject.toml` 已设 `[tool.uv] package = false`（本项目是平铺应用，不装成包）。若报错说明拉到了旧配置，先 `git pull` 再删 `.venv` 重跑 `uv sync` |
| 界面中文显示方块 | 安装中文字体：`sudo apt install fonts-noto-cjk` |
| `.doc` 文档提取不到正文 | 确认安装了 `antiword`；部分老 .doc 只能靠正则回退，效果打折属正常 |
| 提交时把 data/ 加进暂存 | `data/`、`*.db`、`venv*`、`build/`、`dist/` 已在 `.gitignore`，正常情况下不会出现；若出现请检查是否有文件被强制 `git add -f` |
| 公司网络推 GitHub 报 `Failed to connect to github.com port 443` | 公司出口对 GitHub 直连不稳定，已为 git 配置本机代理（**仅对 github.com 生效**，内网 gitlab 直连不受影响）：`git config --global http.https://github.com.proxy http://127.0.0.1:7890`。需本机代理软件（如 Clash）在运行；若代理软件未启动，先启动它再推送 |
| 代理下报 `schannel: failed to receive handshake, SSL/TLS connection failed` | git 走代理时 Windows schannel 后端握手失败，已切换为 OpenSSL 后端：`git config --global http.sslBackend openssl` |

## 五、打包（构建产物）

| 平台 | 脚本 | 说明 |
|---|---|---|
| Windows x64 / x86 | `build.bat [x64\|x86\|all]` | 公司机器上执行，依赖 `venv38` / `venv38_x86` |
| Linux x64 / ARM64 | `build_linux.sh` | Ubuntu 上执行，输出 `RegulationManager_Kylin_<arch>` |
| Linux（容器化） | `Dockerfile.linux` + `build_docker.*` | 基于 Ubuntu 20.04，兼容麒麟 v10 |

> PyInstaller 不能交叉编译：Windows 版只能在 Windows 打，Linux 版只能在 Linux 打。
