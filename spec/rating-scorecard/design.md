# 央行评级标准打分卡模块 — 技术设计文档（Technical Design Document）

> **版本**: 1.0
> **更新日期**: 2026-09-04
> **状态**: Draft（待评审）
> **关联**: [requirements.md](./requirements.md)

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
| `database/models.py`（扩展） | `database/__init__.py` | +6 表模型 |
| `database/migrations.py`（扩展） | `utils/`、`config.RESOURCES_DIR` | 启动建表 + 幂等灌入内置数据 |
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
| PK | (check_id, document_id) | 复合主键 | 参考 document_tags 写法 |

> 软删除文档不可关联（应用层校验，见 AC-E2-04）。

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
5. 用户点击"打开"→ 查 documents.file_path → 沿用 MainWindow 现有 QDesktopServices 外部打开逻辑；文件缺失 → Toast 提示
6. 用户点"编辑"→ 编辑对话框 → scorecard_service.update_*(...) 参数化 UPDATE → 刷新树/详情
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

---

## 4. Component Design

### 4.1 `ScorecardPanel`（ui/scorecard_panel.py，主面板 QWidget）

**职责**：
- 顶部栏：银行类型 `QComboBox`（两个 profile）+ 搜索输入框 + 「搜索/清空」按钮
- 左区：`QTreeWidget` 展示 模块→一级→二级→评级内容 四层（节点存 id 链于 UserRole）
- 右区：检查项详情（评分要点/监管依据/需调阅材料 + 关联制度链接按钮组 + 「编辑」按钮）
- 信号：把"打开制度"委托给 MainWindow 既有逻辑（复用 QDesktopServices 打开）

**依赖**：`scorecard_service`、`Toast`、`ui/styles`、既有制度打开逻辑回调。

**关键行为**：
- 切换银行类型 → 重建左树（AC-E1-02/03）
- 点击任一节点 → 右侧显示该节点下检查项（叶子即详情）（AC-E1-04~06）
- 搜索 → 结果列表（可置于树上方，或独立下拉列表）；点击结果 → `expand + scrollToItem + setCurrentItem` 定位并高亮（AC-E4-02）
- 编辑入口：节点右键菜单（重命名 module/section/item）+ 检查项「编辑」按钮（改字段/关联制度）

### 4.2 编辑/制度选择对话框

- `ScorecardEditDialog`（仿 `AddEditDialog` 风格 QDialog，QSS objectName 复用）：模块/一级/二级改名走 `QInputDialog` 或表单；检查项编辑用多行表单（content/key_points/regulation_basis/review_materials）。
- 制度关联：对话框内嵌「选择关联制度」子对话框——搜索框 + `QListWidget`（数据源 `find_documents`）多选 → 保存时 `set_check_documents` 整体替换。
- 保存均先做非空/重名校验（AC-E3-03~05），成功 Toast「已保存」。

### 4.3 `database/models.py` 扩展 & `models/__init__.py` DTO

- 新增 6 个 ORM 类（见 §2.2），relationship 链带 `cascade="all, delete-orphan"`（按需）。
- DTO 最小集：`ScorecardModuleDTO`（含 children/sections/items/checks 列表或按需惰性查询）、`ScorecardCheckDTO`（全字段 + `documents: List[DocumentData]`）、`SearchHitDTO`。

### 4.4 `database/migrations.py` 扩展

- 现有 `init_database()` 流程末尾追加 `seed_rating_scorecards()`（内部幂等）。
- 建表由 `Base.metadata.create_all` 自动覆盖新模型，无手工 DDL。

---

## 5. Security Design

### 5.1 认证 / 授权
单机本地应用，无账号体系：不适用（与现有模块一致）。

### 5.2 数据保护

| 数据类型 | 保护方式 |
|----------|----------|
| 打分卡编辑输入 | SQLAlchemy 参数化 + 非空/长度校验（AC-E3-03~05）；杜绝拼接 SQL |
| 搜索关键词 | `LIKE` 通配符转义（复用 crud.py 中已有 `%/_` 转义写法） |
| 数据库 | 本地 SQLite（`data/regulation.db`），随现有备份机制覆盖 |
| 关联完整性 | FK 约束 + 应用层校验软删文档（AC-E2-04） |

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
| 日志 | 复用 `logging.getLogger(__name__)`，关键操作（seed 条数、保存/重命名/关联变更）记 INFO；异常记 WARNING/ERROR（沿用现有格式，落 `data/logs/app_YYYYMMDD.log`） |
| 验证 | 单元测试 `tests/test_scorecard_service.py`：seed 幂等、树结构正确、改名重名拒绝、关联替换、搜索命中与定位链（沿用 unittest + 内存 sqlite 测试写法，仿 `test_document_service.py`） |

---

## 8. Revision History

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-09-04 | 初稿：架构/6 表模型/seed 机制/服务接口/UI 组件/安全与测试策略 |
