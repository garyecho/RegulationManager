# 央行评级标准打分卡模块 — 实施任务清单（Implementation Tasks）

> **版本**: 1.0
> **更新日期**: 2026-09-04
> **状态**: Planning
> **关联**: [requirements.md](./requirements.md), [design.md](./design.md)

---

## Overview

按「数据层 → 服务层 → UI → 集成回归」四阶段推进；每个功能任务映射到 requirements.md 的验收标准（AC）与非功能需求（NFR）。

**图例**: 🔴 未开始 · 🟡 进行中 · 🟢 完成 · 🔵 阻塞

---

## Phase A：数据模型与内置初始数据

**工期**: ~4.5h
**目标**: 6 张新表可建、内置两份打分卡数据可幂等灌库

### A.1 ORM 模型与约束

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-A1.1 | 在 `database/models.py` 新增 6 个 ORM 类（scorecards / scorecard_modules / scorecard_sections / scorecard_items / scorecard_checks / scorecard_check_documents），含 FK、UNIQUE(父级+name)、sort_order、created_at | 🔴 | AC-E1-01, AC-E3-05 | 1h |

<details>
<summary>📋 T-A1.1: ORM 模型实现要点</summary>

- 参照既有 `Category`/`Document` 写法（`Column/Integer/String/Text/DateTime/Boolean`），不引入 3.9+ 语法。
- `scorecard_check_documents` 复合主键写法仿 `document_tags`（`PrimaryKeyConstraint`）。
- relationship 链：scorecard → modules（cascade all,delete-orphan）→ sections → items → checks；checks ↔ documents 用 secondary 或显式 association（仿 DocumentTag）。
- 层间 UNIQUE：(scorecard_id,name)、(module_id,name)、(section_id,name) —— 支撑 AC-E3-05 同层重名拒绝。

</details>

### A.2 初始数据生成

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-A2.1 | 开发用转换脚本 `tools/export_scorecard_from_xls.py`：xlrd 读 `doc/*.xls` 两个 sheet → 输出 `resources/rating/scorecard_city.json`、`scorecard_village.json`（层级结构，含 '0' 占位折叠） | 🔴 | AC-E1-01, AC-E1-07 | 2h |
| T-A2.2 | 校验生成的 JSON：两版模块数 9/8、检查项总数 211/136 与 xls 一致；占位行正确归入上方二级指标 | 🔴 | AC-E1-01, AC-E1-07 | 0.5h |

<details>
<summary>📋 T-A2.1: 转换逻辑要点（'0' 占位折叠）</summary>

- xlrd 仅作**开发期**依赖：`uv pip install xlrd`（装进 .venv 即可，**不加入 pyproject 运行时依赖**）。
- 逐行扫描：维护"当前 module/section/item"游标；某列出现非空且非 '0' 文本即切换游标并创建/追加节点；'0' 行继承游标。
- 列 4「评分」跳过；空字段输出 `""`。
- JSON 结构（seed 直接可读）：
```json
{ "name": "城商、农商、民营",
  "modules": [ { "name": "一、公司治理", "sort": 0,
    "sections": [ { "name": "（一）组织架构", "sort": 0,
      "items": [ { "name": "1.加强党的领导。", "sort": 0,
        "checks": [ { "content": "...", "key_points": "...", "regulation_basis": "...", "review_materials": "...", "sort": 0 } ] } ] } ] } ] }
```

</details>

### A.3 幂等灌库

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-A3.1 | `database/migrations.py` 新增 `seed_rating_scorecards()`：scorecards 表为空时按 JSON 依次插入 5 层；`init_database()` 流程末尾调用 | 🔴 | AC-E1-01, NFR-REL-002, NFR-PERF-003 | 1h |

<details>
<summary>📋 T-A3.1: 灌库要点</summary>

- JSON 路径：`config.RESOURCES_DIR / "rating" / "scorecard_{city|village}.json"`（开发/冻结通用）。
- 幂等三重保障：scorecards 空表判断 + 各层 UNIQUE 兜底 + 每次启动重复执行无副作用。
- 灌入条数记 INFO 日志（对齐 NFR 观测要求）。

</details>

---

## Phase B：服务层

**工期**: ~9.5h
**目标**: 浏览/编辑/关联/搜索全部业务逻辑可用、可测

### B.1 浏览查询

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-B1.1 | `models/__init__.py` 新增最小 DTO：ScorecardModuleDTO/ScorecardItemDTO/ScorecardCheckDTO/SearchHitDTO | 🔴 | — | 0.5h |
| T-B1.2 | `core/scorecard_service.py`：get_scorecards / get_tree / get_checks / get_check（含关联制度标题），排序稳定 | 🔴 | AC-E1-01~06 | 1.5h |

### B.2 编辑维护

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-B2.1 | rename_node(kind, node_id, new_name)：module/section/item 改名 + 同父级重名校验 + 非空校验 | 🔴 | AC-E3-01~05 | 1h |
| T-B2.2 | update_check(check_id, **fields)：content/key_points/regulation_basis/review_materials 更新 | 🔴 | AC-E3-01~03 | 0.5h |

### B.3 制度关联

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-B3.1 | set_check_documents(check_id, doc_ids) 整体替换关联；校验文档存在且未软删（is_deleted=False） | 🔴 | AC-E2-01~04 | 1h |
| T-B3.2 | find_documents(keyword)：按标题/文号 LIKE（转义 %/_），过滤软删，供选择器 | 🔴 | AC-E2-01 | 0.5h |

### B.4 搜索

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-B4.1 | search(scorecard_id, keyword)：模块/一级/二级/评级内容/评分要点/依据/材料 七处文本 LIKE；空关键词返回空；返回命中 kind + ids_chain + path + snippet | 🔴 | AC-E4-01~05 | 1.5h |

### B.5 服务层测试

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-B5.1 | `tests/test_scorecard_service.py`：内存 sqlite + 迷你 JSON fixture——seed 幂等、树结构、重名拒绝、关联替换、软删文档拒绝关联、搜索命中与 ids_chain | 🔴 | AC-E1/03/04, NFR-REL | 3h |

---

## Phase C：UI

**工期**: ~13.5h
**目标**: 打分卡面板全交互可用

### C.1 入口

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-C1.1 | `MainWindow`：侧边栏新增导航按钮「🏦 评级打分卡」（nav id 与既有一致），内容区切换显示 ScorecardPanel（仿 stats 面板切换） | 🔴 | AC-E1-01, NFR-USA-001 | 0.5h |

### C.2 主面板与浏览

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-C2.1 | `ui/scorecard_panel.py`：顶部（profile QComboBox + 搜索框 + 清空）+ 左 QTreeWidget 四层树 + 右侧详情容器（QSplitter）；银行类型切换重建树 | 🔴 | AC-E1-02~06, NFR-USA-002 | 3h |
| T-C2.2 | 节点点击 → 右侧展示检查项详情（评分要点/监管依据/需调阅材料），叶子节点直接展示 | 🔴 | AC-E1-05, AC-E1-06 | 1h |

### C.3 制度打开

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-C3.1 | 详情区"已关联制度"链接按钮：点击走 MainWindow 既有打开逻辑（QDesktopServices 外部打开）；文件缺失 → Toast 提示并可解除关联 | 🔴 | AC-E2-05~07 | 1.5h |

### C.4 编辑与关联

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-C4.1 | 节点右键「重命名」+ 检查项「编辑」对话框（仿 AddEditDialog 样式）：非空/重名校验、保存 Toast、刷新 | 🔴 | AC-E3-01~05 | 2.5h |
| T-C4.2 | 制度选择子对话框（搜索框 + 多选列表，数据源 find_documents）→ 保存时 set_check_documents | 🔴 | AC-E2-01~04 | 1.5h |

### C.5 搜索交互

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-C5.1 | 搜索条 + 结果列表（路径展示）；点击结果 → 树展开到该项并选中高亮（expand+scrollTo+setCurrentItem） | 🔴 | AC-E4-01~05 | 2.5h |
| T-C5.2 | 无结果提示、空输入不触发、切换银行类型后清空搜索态 | 🔴 | AC-E4-03, AC-E4-05 | 0.5h |

### C.6 样式打磨

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-C6.1 | 面板/按钮/树样式接入既有 objectName + light.qss 体系（不新增 styles.py 常量） | 🔴 | NFR-USA-001/003 | 1h |

---

## Phase D：集成与回归

**工期**: ~3h
**目标**: 无回归、随包产物正确、文档同步

| ID | 任务 | 状态 | 需求 | 估时 |
|----|------|------|------|------|
| T-D1.1 | 全量回归：既有 9 条测试 + scorecard 新测试全绿；offscreen 无头启动 `main.main()` 冒烟（主窗口→打分卡面板切换） | 🔴 | NFR-REL-001 | 1.5h |
| T-D1.2 | 验证打包：`RegulationManager.spec` 整目录含 `resources/rating/*.json`；Windows/Linux 构建脚本无需改动 | 🔴 | NFR-COST-001 | 0.5h |
| T-D2.1 | 更新 README（功能清单）、AGENTS.md（架构/表清单）、DEVELOPMENT.md（如需） | 🔴 | — | 1h |

---

## Summary

### 任务统计

| 阶段 | 任务数 | 估算工时 |
|------|--------|----------|
| Phase A 数据层 | 3 | 4.5h |
| Phase B 服务层 | 6 | 9.5h |
| Phase C UI | 8 | 13.5h |
| Phase D 集成回归 | 3 | 3h |
| **合计** | **20** | **≈30h** |

### 关键路径

```
T-A1.1(ORM) → T-A2.1/2.2(JSON) → T-A3.1(seed)
     ↓
T-B1.1/1.2(浏览) → T-B2.x(编辑) → T-B3.x(关联) / T-B4.1(搜索) ──┐
     ↓                                                          │
T-B5.1(测试)                                                       │
     ↓                                                            │
T-C1.1(入口) → T-C2.x(面板) → T-C3.1(打开) ────────────────→ C4/C5 并行 → C6
     ↓
T-D1.1(回归) → T-D1.2(打包) → T-D2.1(文档)
```

### 依赖

- **T-B1.x 依赖 T-A3.1**：先有表和 seed 才有查询
- **T-C1.1 依赖 T-B1.x**：面板要调 service
- **T-C3.1 依赖 T-C2.x + 既有打开逻辑**：详情区就绪后接入打开
- **T-C4.1/C4.2 依赖 T-B2.x/T-B3.x**：编辑按钮回调 service
- **T-C5.1 依赖 T-B4.1**：搜索 UI 调 search()
- **T-D1.x 依赖全部 Phase A-C**：最后集成

---

## Revision History

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-09-04 | 初稿：四阶段 20 任务，映射全部 AC/NFR |
