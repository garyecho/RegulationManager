# 央行评级标准打分卡模块 — 技术设计文档（Technical Design Document）

> **版本**: 1.1
> **更新日期**: 2026-09-08
> **状态**: Draft（待评审）
> **关联**: [requirements.md](./requirements.md)
> **变更说明**: 新增 §3.3 自动引用识别服务、更新 §2.2/§4.1/§4.2 超链持久化与 UI 渲染设计

---

## 1. System Architecture

### 1.1 架构总览

本模块完全复用现有桌面应用分层，不引入服务端：

```
┌────────────────────────── Qt 界面层 (ui/) ──────────────────────────┐
│  MainWindow（侧边栏新入口 + 内容区切换）                              │
│    └─ ScorecardPanel（新 ui/scorecard_panel.py）                    │
│         ├─ 顶部：银行类型切换 + 关键词搜索                            │
│         ├─ 左：四层打分卡树（模块→一级→二级→评级内容）                │
│         ├─ 右：检查项详情（评分要点/依据/材料/关联制度）              │
│         └─ 编辑对话框 / 制度选择对话框                                │
└───────────────────────────────┬─────────────────────────────────────┘
                                ▼
┌────────────────────── 业务服务层 (core/) ──────────────────────────┐
│  scorecard_service.py（新增）：树/搜索/编辑/关联，均按 session 调用   │
│  citation_linker.py（新增）：引用识别、文档匹配、超链 HTML 生成        │
└───────────────────────────────┬─────────────────────────────────────┘
                                ▼
┌────────────────────── 数据层 (database/) ─────────────────────────┐
│  models.py（+6 张新表） · crud.py（可选扩展） · migrations.py 建表+灌数│
│  SQLite: data/regulation.db（与 documents 等既有表同库）             │
└────────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 层 | 技术 | 理由 |
|----|------|------|
| UI | PyQt5（复用现有控件/样式/QSS） | 与全库一致，Chinese UI、Toast、QTreeWidget 等现成可用 |
| 业务 | 纯 Python `core/scorecard_service.py` | 跟随现有 service 层模式（document_service 等） |
| 数据 | SQLAlchemy ORM + SQLite（`data/regulation.db`） | 与现有 4 表同库，事务/迁移机制复用 |
| 初始数据 | 资源内静态 JSON（`resources/rating/*.json`）→ 首启灌库 | 离线、幂等；不引入 xls 解析依赖（解析留 v1.1） |

### 1.3 组件依赖

| 新增组件 | 依赖的既有代码 | 说明 |
|----------|----------------|------|
| `ui/scorecard_panel.py` | `ui/styles.py(_FONT)`、`ui/components/toast.py`、`config.py` | 主面板 |
| `core/scorecard_service.py` | `database/get_session`、`database/models.py`、`config.py` | 全部打分卡读写 |
| `database/models.py`（扩展） | `database/__init__.py` | +6 表模型；`scorecard_check_documents` 增加 `is_auto` 字段 |
| `database/migrations.py`（扩展） | `utils/`、`config.RESOURCES_DIR` | 启动建表 + 幂等灌入内置数据；迁移已有 M:N 表增加 `is_auto` 列 |
| `core/citation_linker.py`（新增） | `database/models.py`、CRUD 查询 | 引用解析、文档匹配、HTML 超链生成 |
| `models/__init__.py`（扩展） | — | 新增打分卡 DTO |

---

## 2. Data Model

### 2.1 实体关系

```
scorecards 1 ──< scorecard_modules 1 ──< scorecard_sections 1 ──< scorecard_items
（银行类型）   （模块 col0）           （一级指标 col1）          （二级指标 col2）
                                                                   │
                                                        scorecard_checks 1 ──< scorecard_check_documents >── documents（既有表）
                                                        （评级内容行 col3-7）        M:N 关联制度
```

xls 一行为一条 `scorecard_check`；其 模块/一级/二级 归属由"上方最近非占位（'0'）单元格"落定后写入对应父表；列 4「评分」不建模。

### 2.2 数据库 Schema（新增 6 表，均含 `created_at`）

#### Table: scorecards（打分卡 / 银行类型）

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK autoincrement | |
| name | String(50) | NOT NULL UNIQUE | 如「城商、农商、民营」「村镇银行」 |
| description | String(200) | default '' | |
| created_at | DateTime | NOT NULL default now | |

#### Table: scorecard_modules（模块，xls 列0）

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK | |
| scorecard_id | Integer | FK→scorecards.id, NOT NULL | |
| name | String(200) | NOT NULL | 如「一、公司治理」 |
| sort_order | Integer | NOT NULL default 0 | 按 xls 出现顺序 |
| created_at | DateTime | NOT NULL | |

**Indexes / 约束**: UNIQUE(scorecard_id, name)；INDEX(scorecard_id)

#### Table: scorecard_sections（一级指标，xls 列1）

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK | |
| module_id | Integer | FK→scorecard_modules.id, NOT NULL | |
| name | String(300) | NOT NULL | 如「（一）组织架构」 |
| sort_order | Integer | NOT NULL default 0 | |
| created_at | DateTime | NOT NULL | |

**约束**: UNIQUE(module_id, name)；INDEX(module_id)

#### Table: scorecard_items（二级指标，xls 列2，占位 '0' 已折叠）

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK | |
| section_id | Integer | FK→scorecard_sections.id, NOT NULL | |
| name | String(500) | NOT NULL | 如「1.加强党的领导。」 |
| sort_order | Integer | NOT NULL default 0 | |
| created_at | DateTime | NOT NULL | |

**约束**: UNIQUE(section_id, name)；INDEX(section_id)

#### Table: scorecard_checks（评级内容检查项，xls 一行）

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK | |
| item_id | Integer | FK→scorecard_items.id, NOT NULL | 归属二级指标 |
| content | String(1000) | default '' | 评级内容（列3），可能为空 |
| key_points | Text | default '' | 评分要点（列5） |
| regulation_basis | Text | default '' | 监管制度和条款/依据（列6） |
| review_materials | Text | default '' | 需调阅材料（列7） |
| sort_order | Integer | NOT NULL default 0 | xls 行序 |
| created_at / updated_at | DateTime | NOT NULL | |

**Indexes**: INDEX(item_id)

#### Table: scorecard_check_documents（检查项 ↔ 制度文档 关联）

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| check_id | Integer | FK→scorecard_checks.id | |
| document_id | Integer | FK→documents.id | |
| is_auto | Boolean | NOT NULL default false | true = 系统自动识别关联；false = 人工关联 |
| PK | (check_id, document_id) | 复合主键 | 参考 document_tags 写法 |

> 软删除文档不可关联（应用层校验，见 AC-E2-04）。`is_auto` 用于区分自动识别与人工关联，支持用户手动移除自动关联。

### 2.3 内置初始数据（Seed）

- 数据载体：`resources/rating/scorecard_city.json`、`resources/rating/scorecard_village.json`（由 xls 一次性转换生成，层级 JSON，符合上述表结构）。
- 生成方式：开发期一次性脚本（`tools/export_scorecard_from_xls.py`），用 `xlrd` 读 `doc/*.xls` 输出 JSON；**该脚本为开发工具，不随应用分发**；正式"界面内导入 xls"留 v1.1。
- 灌入时机与幂等：`database/migrations.py` 建表后调用 `seed_rating_scorecards(session)`——`IF scorecards 表为空 THEN 依次插入 5 层数据`；重复执行/每次启动均不产生重复（依据：scorecards 空判断 + 各层 UNIQUE 约束兜底）。
- 打包：PyInstaller spec 已整目录打包 `resources`，JSON 自动随包，`config.RESOURCES_DIR` 统一取路径（开发/冻结模式通用）。

### 2.4 数据流（一次完整用例：搜索→查看→打开制度）

```
1. 用户在打分卡面板输入关键词 → scorecard_service.search(...) LIKE 检索当前 scorecard 全部 5 层文本
2. 返回命中列表（含层级路径与命中节点类型/ID 链）
3. 用户点击命中项 → UI 展开树到该项并选中高亮（scrollTo/expand）
4. 用户选中某检查项 → 右侧详情展示 content/key_points/regulation_basis/review_materials + 关联制度列表
5. **加载详情时自动触发 `citation_linker.sync_auto_links(check_id)`**：解析三个文本字段 → 匹配 documents → 新匹配写入 `scorecard_check_documents(is_auto=true)`；已有关联不覆盖
6. 文本渲染：将纯文本转换为 HTML，命中引用替换为 `<a href="doc://{doc_id}">`，未命中替换为 `<a href="missing://{encoded_citation}" class="missing-link">`
7. 用户点击蓝色链接 → 查 documents.file_path → 沿用 MainWindow 现有 QDesktopServices 外部打开逻辑；文件缺失 → Toast 提示并可解除关联
8. 用户点击灰色/虚线链接 → Toast「未找到对应文件...」
9. 用户点"编辑"→ 编辑对话框 → scorecard_service.update_*(...) 参数化 UPDATE → 保存时再次触发同步 → 刷新树/详情
```

---

## 3. Service API（Python 函数接口，桌面应用无 REST）

### 3.1 函数清单（`core/scorecard_service.py`）

| 函数 | 说明 | 返回 |
|------|------|------|
| `get_scorecards()` | 所有打分卡（银行类型） | `List[ScorecardDTO]` |
| `get_tree(scorecard_id)` | 四层树（含各级排序与检查项） | `List[ScorecardModuleDTO]`（嵌套） |
| `get_checks(item_id)` | 某二级指标下检查项列表（带关联制度标题） | `List[ScorecardCheckDTO]` |
| `get_check(check_id)` | 单条检查项全字段 + 关联文档 | `ScorecardCheckDTO` |
| `rename_node(kind, node_id, new_name)` | kind ∈ {module, section, item}，同父级重名校验 | `bool`（失败 False + Toast） |
| `update_check(check_id, **fields)` | 改 content/key_points/regulation_basis/review_materials | `bool` |
| `set_check_documents(check_id, doc_ids)` | 整体替换关联（0..N），校验文档存在且未软删 | `bool` |
| `search(scorecard_id, keyword)` | 五层字段 LIKE 搜索，空串返回空 | `List[SearchHitDTO]` |
| `find_documents(keyword)` | 制度选择器数据源（按标题/文号 LIKE，过滤软删） | `List[DocumentData]` |

> 以上函数内部统一 `with get_session()` 提交/回滚；编辑类函数沿用 document_service 的异常包裹风格（失败记日志、返回 False）。

### 3.2 入参/响应示例

```python
# 搜索命中结构
ScorecardHit = {
    "kind": "check",            # module | section | item | check
    "id": 12,
    "ids_chain": [3, 7, 9, 12], # module/section/item/check 的 ID 链，用于树定位
    "path": "一、公司治理 / （一）组织架构 / 1.加强党的领导。 / 1.未将党建工作要求纳入公司章程。",
    "matched_field": "key_points",
    "snippet": "...未将党建工作要求纳入公司章程...",
}
```

### 3.3 引用识别与自动超链服务（`core/citation_linker.py`）

新增独立模块，职责单一：把文本里的制度引用转成可点击超链，并持久化匹配结果。

| 函数/类 | 说明 | 返回 |
|---------|------|------|
| `Citation` (dataclass) | 字段：`raw` 原文、`title` 书名号线内文本、`doc_no` 文号（可为 None） | — |
| `extract_citations(text: str) -> List[Citation]` | 正则提取文本中所有制度引用 | `List[Citation]` |
| `find_document(citation: Citation, session) -> Optional[int]` | 按文号精确 → 标题包含 → 标题相似匹配 documents；返回 doc_id | `Optional[int]` |
| `sync_auto_links(check_id: int) -> Tuple[int, int]` | 扫描检查项三字段，写入新匹配；返回 `(matched_count, unmatched_count)` | `Tuple[int, int]` |
| `render_html(text: str, hits: List[Tuple[int, int, Optional[int]]]) -> str` | 将文本切片替换为 `<a>` 标签；未匹配 doc_id 为 None | HTML 字符串 |

#### 引用识别规则

```
模式 A（完整）: 《([^《》]+)》[（(]([^）)]+号文?)[）)]
模式 B（仅标题）: 《([^《》]+)》
模式 C（仅文号）: [（(]([^）)]+号文?)[）)]
```

- 文号内可能含中文全角括号 `〔〕`、圆括号 `()`、方括号 `[]`，统一归一化后再匹配。
- 多个引用在同一段文本中独立识别，按出现位置排序。
- 标题/文号前后允许存在空格、顿号、逗号等常规标点。

#### 文档匹配算法

1. **文号归一化**：去除空格、统一括号类型、统一全半角，如 `银保监发〔2021〕14号` 与 `银保监发(2021)14号` 视为等价。
2. **匹配优先级**（依次降级）：
   - 文档 `doc_no` 与引用 `doc_no` 归一化后完全相等。
   - 文档 `title` 包含引用 `title`（去除书名号）。
   - 文档 `title` 与引用 `title` 的相似度 ≥ 0.75（`difflib.SequenceMatcher.ratio()`）。
3. **多候选处理**：若仍有多个候选，取 `created_at` 最新的一份；AC-E5-05 的候选列表悬停/右键作为可选增强。

#### HTML 渲染约定

```html
<!-- 已匹配 -->
<a href="doc://123" style="color:#0066cc;text-decoration:underline;">《银行保险机构公司治理准则》（银保监发〔2021〕14 号）</a>

<!-- 未匹配 -->
<a href="missing://%E9%93%B6%E4%BF%9D%E7%9B%91%E5%8F%91%E3%80%942021%E3%80%9514%E5%8F%B7" style="color:#999;border-bottom:1px dashed #999;text-decoration:none;cursor:not-allowed;">《...</a>
```

- 使用自定义 URL scheme，避免与真实 HTTP 链接混淆。
- `QTextBrowser`/`QLabel` 的 `linkActivated` 信号负责拦截并分发到 `MainWindow` 的打开逻辑。

---

## 4. Component Design

### 4.1 `ScorecardPanel`（ui/scorecard_panel.py，主面板 QWidget）

**职责**：
- 顶部栏：银行类型 `QComboBox`（两个 profile）+ 搜索输入框 + 「搜索/清空」按钮
- 左区：`QTreeWidget` 展示 模块→一级→二级→评级内容 四层（节点存 id 链于 UserRole）
- 右区：检查项详情（评分要点/监管依据/需调阅材料以 `QTextBrowser` 展示 HTML 超链 + 关联制度链接按钮组 + 「编辑」按钮）
- 信号：把"打开制度"委托给 MainWindow 既有逻辑（复用 QDesktopServices 打开）；拦截 `linkActivated` 处理 `doc://` 与 `missing://` scheme

**依赖**：`scorecard_service`、`Toast`、`ui/styles`、既有制度打开逻辑回调。

**关键行为**：
- 切换银行类型 → 重建左树（AC-E1-02/03）
- 点击任一节点 → 右侧显示该节点下检查项（叶子即详情）（AC-E1-04~06）
- 选中检查项详情时 → 调用 `citation_linker.sync_auto_links(check_id)` 生成/更新自动关联 → 用 `render_html` 渲染超链文本（AC-E5-01~04, AC-E5-10~13）
- 搜索 → 结果列表（可置于树上方，或独立下拉列表）；点击结果 → `expand + scrollToItem + setCurrentItem` 定位并高亮（AC-E4-02）
- 编辑入口：节点右键菜单（重命名 module/section/item）+ 检查项「编辑」按钮（改字段/关联制度）；保存后再同步一次自动关联
- 超链点击：
  - `doc://{id}` → 调用 MainWindow 打开逻辑
  - `missing://{encoded}` → Toast「未找到对应文件...」（AC-E5-07~09）

### 4.2 编辑/制度选择对话框

- `ScorecardEditDialog`（仿 `AddEditDialog` 风格 QDialog，QSS objectName 复用）：模块/一级/二级改名走 `QInputDialog` 或表单；检查项编辑用多行表单（content/key_points/regulation_basis/review_materials）。
- 制度关联：对话框内嵌「选择关联制度」子对话框——搜索框 + `QListWidget`（数据源 `find_documents`）多选 → 保存时 `set_check_documents` 整体替换。
- 自动关联展示：在编辑对话框的关联制度列表中，用图标或标签区分 `is_auto=true`（自动识别）与 `is_auto=false`（人工）；允许用户删除自动关联。
- 保存均先做非空/重名校验（AC-E3-03~05），成功 Toast「已保存」；保存成功后调用 `sync_auto_links` 重新识别（AC-E5-14）。

### 4.3 `database/models.py` 扩展 & `models/__init__.py` DTO

- 新增 6 个 ORM 类（见 §2.2），relationship 链带 `cascade="all, delete-orphan"`（按需）。
- DTO 最小集：`ScorecardModuleDTO`（含 children/sections/items/checks 列表或按需惰性查询）、`ScorecardCheckDTO`（全字段 + `documents: List[DocumentData]`）、`SearchHitDTO`。

### 4.4 `database/migrations.py` 扩展

- 现有 `init_database()` 流程末尾追加 `seed_rating_scorecards()`（内部幂等）。
- 建表由 `Base.metadata.create_all` 自动覆盖新模型，无手工 DDL。
- **v1.1 迁移**：若 `scorecard_check_documents` 表已存在但缺少 `is_auto` 列，在 `init_database()` 中执行 `ALTER TABLE scorecard_check_documents ADD COLUMN is_auto BOOLEAN NOT NULL DEFAULT 0`，保证旧数据库兼容。

---

## 5. Security Design

### 5.1 认证 / 授权
单机本地应用，无账号体系：不适用（与现有模块一致）。

### 5.2 数据保护

| 数据类型 | 保护方式 |
|----------|----------|
| 打分卡编辑输入 | SQLAlchemy 参数化 + 非空/长度校验（AC-E3-03~05）；杜绝拼接 SQL |
| 搜索关键词 | `LIKE` 通配符转义（复用 crud.py 中已有 `%/_` 转义写法） |
| 引用识别输入 | 纯文本正则提取，不做 eval/exec；渲染前对 HTML 特殊字符转义，防 XSS 类注入 |
| 数据库 | 本地 SQLite（`data/regulation.db`），随现有备份机制覆盖 |
| 关联完整性 | FK 约束 + 应用层校验软删文档（AC-E2-04）；`is_auto` 字段区分自动/人工关联 |

---

## 6. Infrastructure / 部署

### 6.1 部署
沿用现有产物形态：Windows `build.bat`（PyInstaller）、Linux `build_linux.sh`；新资源 `resources/rating/*.json` 随整目录打包，无新增部署步骤。

### 6.2 运行期配置
无新增环境变量；JSON 目录取 `config.RESOURCES_DIR / "rating"`。

---

## 7. 观测 / 日志

| 类型 | 实现 |
|------|------|
| 日志 | 复用 `logging.getLogger(__name__)`，关键操作（seed 条数、保存/重命名/关联变更、自动识别匹配/未匹配数）记 INFO；异常记 WARNING/ERROR（沿用现有格式，落 `data/logs/app_YYYYMMDD.log`） |
| 验证 | 单元测试 `tests/test_scorecard_service.py`：seed 幂等、树结构正确、改名重名拒绝、关联替换、搜索命中与定位链；**新增** `tests/test_citation_linker.py`：正则提取、文号归一化、匹配优先级、HTML 渲染（沿用 unittest + 内存 sqlite 测试写法） |

---

## 8. Revision History

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-09-04 | 初稿：架构/6 表模型/seed 机制/服务接口/UI 组件/安全与测试策略 |
| 1.1 | 2026-09-08 | 新增自动引用识别设计：`core/citation_linker.py`、`is_auto` 字段、超链 HTML 渲染、匹配算法 |
