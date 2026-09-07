"""
央行评级标准打分卡服务层单元测试
"""
import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from core import scorecard_service
from database.models import (
    Base, Scorecard, ScorecardModule, ScorecardSection, ScorecardItem, ScorecardCheck,
    Document,
)


class ScorecardServiceTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self.engine = create_engine("sqlite:///" + str(self.data_dir / "test.db"))

        @event.listens_for(self.engine, "connect")
        def enable_fk(dbapi_conn, connection_record):
            del connection_record
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

        # 构造迷你打分卡：1 模块 / 1 一级 / 2 二级 / 3 检查项 + 1 份制度文档
        with self.factory() as session:
            sc = Scorecard(name="测试打分卡", description="测试用")
            session.add(sc)
            session.flush()
            self._sc_id = sc.id

            m1 = ScorecardModule(scorecard_id=sc.id, name="一、公司治理", sort_order=0)
            session.add(m1)
            session.flush()
            self._m1_id = m1.id

            s1 = ScorecardSection(module_id=m1.id, name="（一）组织架构", sort_order=0)
            session.add(s1)
            session.flush()
            self._s1_id = s1.id

            i1 = ScorecardItem(section_id=s1.id, name="1.加强党的领导。", sort_order=0)
            i2 = ScorecardItem(section_id=s1.id, name="2.股权结构科学合理。", sort_order=1)
            session.add_all([i1, i2])
            session.flush()
            self._i1_id, self._i2_id = i1.id, i2.id

            c1 = ScorecardCheck(
                item_id=i1.id, content="1.未将党建工作要求纳入公司章程。",
                key_points="根据《银行保险机构公司治理准则》第九条",
                regulation_basis="银保监发〔2021〕14号", review_materials="公司章程", sort_order=0,
            )
            c2 = ScorecardCheck(item_id=i1.id, content="2.未能落实双向交叉任职。", sort_order=1)
            c3 = ScorecardCheck(
                item_id=i2.id, content="1.单一最大股东持股占比。",
                key_points="单一股东持股占比不超过30%", sort_order=0,
            )
            session.add_all([c1, c2, c3])
            session.flush()
            self._c1_id, self._c2_id, self._c3_id = c1.id, c2.id, c3.id

            doc = Document(
                title="公司章程", file_path="documents/charter.pdf",
                original_name="charter.pdf", file_type="pdf",
            )
            session.add(doc)
            session.flush()
            self._doc_id = doc.id

        # 让 service 使用测试库
        self._patcher = patch.object(scorecard_service, "get_session", self.factory)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    @contextlib.contextmanager
    def factory(self):
        """与生产 get_session 同语义：正常退出即提交"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ── 引用识别与自动超链 ──

    def test_sync_auto_links_persists_and_idempotent(self):
        """引用匹配 → 自动落库 is_auto=True → 重复执行不重复插"""
        with self.factory() as session:
            session.add(Document(
                title="银行保险机构公司治理准则", doc_no="银保监发〔2021〕14号",
                file_path="documents/gov.pdf", original_name="gov.pdf", file_type="pdf",
            ))
        added = scorecard_service.sync_auto_links(self._c1_id)
        self.assertEqual(1, added)  # key_points 与 regulation_basis 指向同一文档，只插一条
        self.assertEqual(0, scorecard_service.sync_auto_links(self._c1_id))  # 幂等

        from database.models import ScorecardCheckDocument
        with self.factory() as session:
            link = session.query(ScorecardCheckDocument).filter_by(check_id=self._c1_id).one()
            self.assertEqual(True, bool(link.is_auto))

    def test_render_linked_html_match_and_missing(self):
        with self.factory() as session:
            session.add(Document(
                title="银行保险机构公司治理准则", doc_no="银保监发〔2021〕14号",
                file_path="documents/gov.pdf", original_name="gov.pdf", file_type="pdf",
            ))
        html = scorecard_service.render_linked_html(
            "依据《银行保险机构公司治理准则》（银保监发〔2021〕14 号）及《未知文件》")
        self.assertIn('href="doc://', html)      # 已匹配 → 蓝链
        self.assertIn('href="missing://', html)  # 未匹配 → 灰链
        self.assertIn('#999999', html)

    def test_ignore_auto_links_prevents_resync(self):
        """移除自动关联 → 记入忽略清单 → 再次 sync 不会重新插入"""
        with self.factory() as session:
            session.add(Document(
                title="银行保险机构公司治理准则", doc_no="银保监发〔2021〕14号",
                file_path="documents/gov.pdf", original_name="gov.pdf", file_type="pdf",
            ))
        added = scorecard_service.sync_auto_links(self._c1_id)
        self.assertEqual(1, added)

        # 模拟用户移除该自动关联
        from database.models import ScorecardCheckDocument
        with self.factory() as session:
            link = session.query(ScorecardCheckDocument).filter_by(check_id=self._c1_id).one()
            session.delete(link)

        # 记入忽略清单
        scorecard_service.ignore_auto_links(self._c1_id, [link.document_id])

        # 再次 sync 不会重新插入
        self.assertEqual(0, scorecard_service.sync_auto_links(self._c1_id))

        # 清空忽略清单后重新识别 → 恢复
        scorecard_service.clear_ignored_auto_ids(self._c1_id)
        added2 = scorecard_service.sync_auto_links(self._c1_id)
        self.assertEqual(1, added2)

    # ── 查询 ──

    def test_get_scorecards(self):
        cards = scorecard_service.get_scorecards()
        self.assertEqual(1, len(cards))
        self.assertEqual("测试打分卡", cards[0].name)

    def test_get_tree_structure(self):
        tree = scorecard_service.get_tree(self._sc_id)
        self.assertEqual(1, len(tree), "1 个模块")
        module = tree[0]
        self.assertEqual("一、公司治理", module.name)
        self.assertEqual(1, len(module.children), "1 个一级指标")
        section = module.children[0]
        self.assertEqual("（一）组织架构", section.name)
        self.assertEqual(2, len(section.children), "2 个二级指标")
        # 第一个二级指标下有 2 个检查项
        item = section.children[0]
        self.assertEqual("1.加强党的领导。", item.name)
        self.assertEqual(2, len(item.checks))
        self.assertEqual("1.未将党建工作要求纳入公司章程。", item.checks[0].content)
        self.assertEqual("2.未能落实双向交叉任职。", item.checks[1].content)

    def test_get_checks(self):
        checks = scorecard_service.get_checks(self._i1_id)
        self.assertEqual(2, len(checks))

    def test_get_check(self):
        check = scorecard_service.get_check(self._c1_id)
        self.assertIsNotNone(check)
        self.assertEqual("1.未将党建工作要求纳入公司章程。", check.content)
        self.assertEqual("银保监发〔2021〕14号", check.regulation_basis)

    def test_get_check_missing(self):
        self.assertIsNone(scorecard_service.get_check(99999))

    # ── 编辑 ──

    def test_rename_node_success(self):
        self.assertTrue(scorecard_service.rename_node("module", self._m1_id, "一、治理"))
        with self.factory() as sess:
            m = sess.get(ScorecardModule, self._m1_id)
            self.assertEqual("一、治理", m.name)

    def test_rename_node_empty_rejected(self):
        self.assertFalse(scorecard_service.rename_node("module", self._m1_id, ""))

    def test_rename_node_duplicate_rejected(self):
        """同一父级下重名应被拒绝"""
        # 二级指标 i2 想改成 i1 的名字（同属 s1）→ 拒绝
        self.assertFalse(scorecard_service.rename_node("item", self._i2_id, "1.加强党的领导。"))
        with self.factory() as sess:
            item = sess.get(ScorecardItem, self._i2_id)
            self.assertEqual("2.股权结构科学合理。", item.name, "名称不应被改动")

    def test_rename_node_same_name_is_noop(self):
        self.assertTrue(scorecard_service.rename_node("item", self._i1_id, "1.加强党的领导。"))

    def test_rename_node_unknown_kind(self):
        self.assertFalse(scorecard_service.rename_node("unknown", 1, "新名称"))

    def test_update_check(self):
        self.assertTrue(scorecard_service.update_check(self._c1_id, key_points="新评分要点"))
        with self.factory() as sess:
            c = sess.get(ScorecardCheck, self._c1_id)
            self.assertEqual("新评分要点", c.key_points)

    def test_update_check_empty_content_rejected(self):
        self.assertFalse(scorecard_service.update_check(self._c1_id, content=""))

    def test_update_check_unknown_field_ignored(self):
        self.assertTrue(scorecard_service.update_check(self._c1_id, content="A", nope="B"))
        with self.factory() as sess:
            c = sess.get(ScorecardCheck, self._c1_id)
            self.assertEqual("A", c.content)

    # ── 关联 ──

    def test_set_check_documents(self):
        self.assertTrue(scorecard_service.set_check_documents(self._c1_id, [self._doc_id]))
        check = scorecard_service.get_check(self._c1_id)
        self.assertEqual(1, len(check.documents))
        self.assertEqual("公司章程", check.documents[0].title)

    def test_set_check_documents_replace(self):
        scorecard_service.set_check_documents(self._c1_id, [self._doc_id])
        self.assertTrue(scorecard_service.set_check_documents(self._c1_id, []))
        check = scorecard_service.get_check(self._c1_id)
        self.assertEqual(0, len(check.documents))

    def test_set_check_documents_ignores_deleted(self):
        """软删除的文档不应被关联"""
        with self.factory() as sess:
            doc = sess.get(Document, self._doc_id)
            doc.is_deleted = True
            sess.flush()
        self.assertTrue(scorecard_service.set_check_documents(self._c1_id, [self._doc_id]))
        check = scorecard_service.get_check(self._c1_id)
        self.assertEqual(0, len(check.documents))

    def test_find_documents(self):
        docs = scorecard_service.find_documents("章程")
        self.assertEqual(1, len(docs))
        self.assertEqual("公司章程", docs[0].title)

    def test_find_documents_empty_keyword(self):
        docs = scorecard_service.find_documents("")
        self.assertGreaterEqual(len(docs), 1)

    def test_find_documents_ignores_deleted(self):
        with self.factory() as sess:
            doc = sess.get(Document, self._doc_id)
            doc.is_deleted = True
            sess.flush()
        docs = scorecard_service.find_documents("章程")
        self.assertEqual(0, len(docs))

    # ── 搜索 ──

    def test_search_hits_module(self):
        hits = scorecard_service.search(self._sc_id, "公司治理")
        self.assertTrue(any(h.kind == "module" for h in hits))

    def test_search_hits_check_content(self):
        hits = scorecard_service.search(self._sc_id, "党建工作")
        self.assertTrue(any(h.kind == "check" and "党建工作" in h.snippet for h in hits))

    def test_search_hits_key_points(self):
        hits = scorecard_service.search(self._sc_id, "股东持股")
        self.assertTrue(any(h.kind == "check" and "股东持股" in h.snippet for h in hits))

    def test_search_empty_keyword(self):
        self.assertEqual(0, len(scorecard_service.search(self._sc_id, "")))

    def test_search_no_match(self):
        self.assertEqual(0, len(scorecard_service.search(self._sc_id, "不可能匹配到任何内容abcxyzxyz")))

    def test_search_ids_chain(self):
        hits = scorecard_service.search(self._sc_id, "党建工作")
        hit = next(h for h in hits if h.kind == "check")
        # ids_chain: [module_id, section_id, item_id, check_id]
        self.assertEqual(4, len(hit.ids_chain))
        self.assertEqual(hit.ids_chain[3], hit.id)


if __name__ == "__main__":
    unittest.main()