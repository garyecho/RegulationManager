"""引用识别/匹配/渲染 最小自检（纯函数，不依赖 DB）"""
import unittest
from unittest.mock import patch
from collections import namedtuple

from core.scorecard_service import (
    _norm_no, extract_citations, match_document, render_linked_html,
)

FakeDoc = namedtuple("FakeDoc", "id title doc_no")

DOCS = [
    FakeDoc(1, "银行保险机构公司治理准则", "银保监发〔2021〕14号"),
    FakeDoc(2, "商业银行内部控制指引", "银保监发〔2019〕18号"),
    FakeDoc(3, "关于进一步加强银行保险机构公司治理准则实施的通知", ""),
]


class TestExtract(unittest.TestCase):
    def test_full(self):
        self.assertEqual(
            extract_citations("依据《银行保险机构公司治理准则》（银保监发〔2021〕14 号）执行"),
            [("银行保险机构公司治理准则", "银保监发〔2021〕14 号")],
        )

    def test_title_only(self):
        self.assertEqual(extract_citations("见《商业银行内部控制指引》相关要求"),
                         [("商业银行内部控制指引", None)])

    def test_no_only(self):
        self.assertEqual(extract_citations("按（银保监发〔2019〕18号）执行"),
                         [(None, "银保监发〔2019〕18号")])

    def test_mixed_multiple(self):
        cs = extract_citations("《A准则》（银保监发〔2021〕14号）及《B指引》与（某文〔2020〕1号）")
        self.assertEqual(len(cs), 3)

    def test_no_false_positive(self):
        self.assertEqual(extract_citations("步骤（一）和（二）"), [])


class TestMatch(unittest.TestCase):
    def test_doc_no_beats_title(self):
        # 文号精确命中 #1，即使标题也含
        doc = match_document("银行保险机构公司治理准则", "银保监发〔2021〕14 号", DOCS)
        self.assertEqual(doc.id, 1)

    def test_no_bracket_equivalence(self):
        self.assertEqual(_norm_no("银保监发〔2021〕14号"), _norm_no("银保监发(2021)14 号"))

    def test_title_containment(self):
        doc = match_document("银行保险机构公司治理准则", None, DOCS)
        self.assertEqual(doc.id, 1)

    def test_similarity(self):
        doc = match_document("银行保险机构公司治理准则（修订）", None, DOCS)
        self.assertEqual(doc.id, 1)

    def test_no_match(self):
        self.assertIsNone(match_document("不存在的文件", None, DOCS))


class TestRender(unittest.TestCase):
    def test_matched_link(self):
        with patch("core.scorecard_service._resolve_citation", return_value=42):
            out = render_linked_html("依据《银行保险机构公司治理准则》（银保监发〔2021〕14号）")
        self.assertIn('href="doc://42"', out)

    def test_missing_link(self):
        with patch("core.scorecard_service._resolve_citation", return_value=None):
            out = render_linked_html("见《不存在的文件》")
        self.assertIn('href="missing://', out)
        self.assertIn("#999999", out)

    def test_plain_text_untouched(self):
        self.assertEqual(render_linked_html("普通文本（一）"), "普通文本（一）")


if __name__ == "__main__":
    unittest.main()
