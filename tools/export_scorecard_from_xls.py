"""
开发期一次性工具：把央行评级打分卡 xls 转成内置 JSON 初始数据。

用法（需先 `uv pip install xlrd`，xlrd 不进运行时依赖）：
    .venv/bin/python tools/export_scorecard_from_xls.py

输出：resources/rating/scorecard_city.json、resources/rating/scorecard_village.json
"""
import json
import os
import sys

import xlrd

XLS_PATH = "doc/延边州分行-附件：央行评级专业评价指标体系征求意见表.xls"
OUT_DIR = os.path.join("resources", "rating")

# sheet 名 → (输出文件名, 打分卡名称)
SHEETS = {
    "城商、农商、民营": ("scorecard_city.json", "城商、农商、民营"),
    "村镇银行": ("scorecard_village.json", "村镇银行"),
}

# 固定列（两个 sheet 一致）
COL_MODULE, COL_SECTION, COL_ITEM = 0, 1, 2

# 其余字段按表头文本动态定位（城商版 7 列无"评分"空列，村镇版 8 列有，列号不同）
HEADER_KEYWORDS = {
    "content": ("评级内容",),
    "key_points": ("评分要点",),
    "basis": ("监管制度", "条款", "依据"),
    "materials": ("需调阅", "调阅材料", "材料"),
}

PLACEHOLDER = "0"  # 二级指标列的占位值，表示继承上一个二级指标


def resolve_cols(sheet):
    """从表头行（第 2 行）解析各字段所在列号，返回 {field: col}"""
    cols = {"module": COL_MODULE, "section": COL_SECTION, "item": COL_ITEM}
    header_row = 1
    for field, keywords in HEADER_KEYWORDS.items():
        found = None
        for c in range(sheet.ncols):
            header = str(sheet.cell_value(header_row, c)).strip()
            if any(kw in header for kw in keywords):
                found = c
                break
        if found is None:
            raise ValueError("找不到列：%s（sheet=%s）" % (field, sheet.name))
        cols[field] = found
    return cols


def cell(sheet, row, col):
    """取单元格文本，去空白；占位/空值返回 ''"""
    if col >= sheet.ncols:
        return ""
    value = sheet.cell_value(row, col)
    if isinstance(value, float):
        value = str(int(value)) if value.is_integer() else str(value)
    text = str(value).strip()
    return "" if text == PLACEHOLDER else text


def convert_sheet(sheet, scorecard_name):
    """一行 = 一条检查项；模块/一级/二级取上方最近的非占位值。
    key_points/basis/materials 列如果是合并单元格，xlrd 只在第一行有值，
    后续行为空——向上继承同 item 内上一行的值（模拟合并单元格的向下填充语义）。
    """
    cols = resolve_cols(sheet)
    scorecard = {"name": scorecard_name, "modules": []}
    module = section = item = None
    # 合并单元格向下填充：同 item 内记住上一行的值
    last_key_points = last_basis = last_materials = ""

    for row in range(2, sheet.nrows):  # 0 标题、1 表头
        module_name = cell(sheet, row, cols["module"])
        section_name = cell(sheet, row, cols["section"])
        item_name = cell(sheet, row, cols["item"])

        if module_name:
            module = {"name": module_name, "sort": len(scorecard["modules"]), "sections": []}
            scorecard["modules"].append(module)
            section = item = None
        if section_name:
            if module is None:
                continue
            section = {"name": section_name, "sort": len(module["sections"]), "items": []}
            module["sections"].append(section)
            item = None
        if item_name:
            if section is None:
                continue
            item = {"name": item_name, "sort": len(section["items"]), "checks": []}
            section["items"].append(item)
            last_key_points = last_basis = last_materials = ""

        content = cell(sheet, row, cols["content"])
        key_points = cell(sheet, row, cols["key_points"]) or last_key_points
        basis = cell(sheet, row, cols["basis"]) or last_basis
        materials = cell(sheet, row, cols["materials"]) or last_materials
        if not any([content, key_points, basis, materials]):
            continue
        if item is None:
            continue
        last_key_points = key_points
        last_basis = basis
        last_materials = materials
        item["checks"].append({
            "content": content,
            "key_points": key_points,
            "regulation_basis": basis,
            "review_materials": materials,
            "sort": len(item["checks"]),
        })

    return scorecard


def stats(scorecard):
    modules = scorecard["modules"]
    sections = [s for m in modules for s in m["sections"]]
    items = [i for s in sections for i in s["items"]]
    checks = [c for i in items for c in i["checks"]]
    return len(modules), len(sections), len(items), len(checks)


def main():
    if not os.path.exists(XLS_PATH):
        sys.exit("找不到 xls：%s（请在项目根目录运行）" % XLS_PATH)

    workbook = xlrd.open_workbook(XLS_PATH)
    os.makedirs(OUT_DIR, exist_ok=True)

    for sheet in workbook.sheets():
        key = sheet.name.strip()
        if key not in SHEETS:
            print("跳过未知 sheet：%r" % sheet.name)
            continue
        filename, scorecard_name = SHEETS[key]
        data = convert_sheet(sheet, scorecard_name)
        out_path = os.path.join(OUT_DIR, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("%s → %s  模块%d / 一级%d / 二级%d / 检查项%d" % ((scorecard_name, out_path) + stats(data)))


if __name__ == "__main__":
    main()
