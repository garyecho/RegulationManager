# DEVELOPMENT.md — 开发环境与提交流程

本文件说明本项目在两台机器（公司 Windows + 家里 Ubuntu）上的开发环境搭建，
以及日常提交 / 推送代码的标准流程。

- 技术栈：PyQt5 + SQLAlchemy + SQLite
- 依赖（见 `pyproject.toml` / `uv.lock`）：PyQt5、SQLAlchemy、PyMuPDF、python-docx、jieba

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
| 家里 Ubuntu | 3.12 | PyQt5 5.15.11 官方 wheel 最高支持 3.12；Ubuntu 默认 3.13 装不上 PyQt5 |

代码使用 `typing` 兼容写法（`Dict` / `List`），在 3.8 ~ 3.12 均可运行。
**不要**在代码里使用 3.9+ 语法（如 `dict[int, int]`），否则公司 3.8 环境会报错。

## 一、家里 Ubuntu 跑通

```bash
# 1. 安装 uv（Python 版本 / 依赖管理）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆仓库（走 GitHub）
git clone https://github.com/garyecho/RegulationManager.git
cd RegulationManager

# 3. 固定 Python 3.12 并创建虚拟环境、安装依赖
uv python install 3.12
uv sync

# 4. 系统依赖：.doc 老格式提取 + 中文字体（否则中文显示方块）
sudo apt install antiword fonts-noto-cjk

# 5. 启动（data/ 目录与数据库首次运行自动创建）
uv run python main.py
```

跑通自检：窗口正常打开、能导入 pdf/docx 文档、搜索能出结果。

> `uv python install 3.12` 只安装 Python 解释器本体；
> `uv sync` 才会创建项目内的 `.venv/` 虚拟环境并安装依赖（与公司 `venv38` 同理，只是工具不同）。

## 二、公司 Windows 环境

沿用现有虚拟环境即可（`venv38` 64 位 / `venv38_x86` 32 位，见 `setup_x86.bat`）：

```bash
venv38\Scripts\python.exe main.py
```

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
git push github master         # 家里：内网连不上，推 GitHub
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
| 启动报 `could not load platform plugin "xcb"` | Ubuntu 缺 Qt 系统库，安装 `libxcb-xinerama0 libegl1 libxkbcommon0 libgl1` 后重试 |
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
