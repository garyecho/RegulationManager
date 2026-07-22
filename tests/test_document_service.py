import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from core import document_service
from database.models import Base, Document, DocumentTag, Tag
from utils import search_engine


class DocumentServiceRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self.engine = create_engine("sqlite:///" + str(self.data_dir / "test.db"))

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(dbapi_conn, connection_record):
            del connection_record
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

        with self.session() as session:
            session.execute(text("""
                CREATE VIRTUAL TABLE documents_fts
                USING fts5(title, doc_no, department, issuing_org, description, content_text)
            """))

        self.patches = [
            patch.object(document_service, "get_session", self.session),
            patch.object(search_engine, "get_session", self.session),
            patch.object(document_service.config, "DATA_DIR", self.data_dir),
        ]
        for active_patch in self.patches:
            active_patch.start()

    def tearDown(self):
        for active_patch in reversed(self.patches):
            active_patch.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    @contextmanager
    def session(self):
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_document(self, title, file_path="documents/shared.pdf", tag=None):
        with self.session() as session:
            doc = Document(
                title=title,
                file_path=file_path,
                original_name=Path(file_path).name,
                file_type="pdf",
            )
            session.add(doc)
            session.flush()
            doc_id = doc.id
            if tag is not None:
                session.add(DocumentTag(document_id=doc_id, tag_id=tag))
            return doc_id

    def test_update_document_refreshes_fts_content(self):
        doc_id = self.create_document("旧标题")
        document_service._reindex_document(doc_id)

        updated = document_service.update_document(
            doc_id,
            title="新标题",
            description="新备注",
        )

        self.assertEqual("新标题", updated.title)
        old_ids, _, _ = search_engine.search_fts("旧标题")
        new_ids, _, _ = search_engine.search_fts("新标题")
        self.assertNotIn(doc_id, old_ids)
        self.assertIn(doc_id, new_ids)

    def test_non_indexed_update_does_not_reindex(self):
        doc_id = self.create_document("保持不变")
        with patch("utils.search_engine.index_document_in_session") as reindex:
            document_service.update_document(doc_id, category_id=None)
        reindex.assert_not_called()

    def test_fts_failure_rolls_back_document_update(self):
        doc_id = self.create_document("原始标题")
        with patch(
            "utils.search_engine.index_document_in_session",
            side_effect=RuntimeError("index failed"),
        ):
            updated = document_service.update_document(doc_id, title="不应保存")

        self.assertIsNone(updated)
        with self.session() as session:
            self.assertEqual("原始标题", session.get(Document, doc_id).title)

    def test_permanent_delete_removes_tag_association_after_commit(self):
        with self.session() as session:
            tag = Tag(name="测试标签", usage_count=1)
            session.add(tag)
            session.flush()
            tag_id = tag.id

        file_path = self.data_dir / "documents" / "tagged.pdf"
        file_path.parent.mkdir(parents=True)
        file_path.write_bytes(b"pdf")
        doc_id = self.create_document(
            "带标签制度", file_path="documents/tagged.pdf", tag=tag_id
        )
        document_service._reindex_document(doc_id)

        result = document_service.batch_permanent_delete([doc_id])

        self.assertEqual({"success": 1, "failed": 0}, result)
        self.assertFalse(file_path.exists())
        with self.session() as session:
            self.assertIsNone(session.get(Document, doc_id))
            association_count = session.query(DocumentTag).filter(
                DocumentTag.document_id == doc_id
            ).count()
            self.assertEqual(0, association_count)
            self.assertEqual(0, session.get(Tag, tag_id).usage_count)
            fts_count = session.execute(text(
                "SELECT COUNT(*) FROM documents_fts WHERE rowid = :id"
            ), {"id": doc_id}).scalar()
            self.assertEqual(0, fts_count)

    def test_fts_delete_failure_rolls_back_permanent_delete(self):
        file_path = self.data_dir / "documents" / "rollback.pdf"
        file_path.parent.mkdir(parents=True)
        file_path.write_bytes(b"pdf")
        doc_id = self.create_document(
            "删除失败回滚", file_path="documents/rollback.pdf"
        )

        with patch(
            "utils.search_engine.remove_from_index_in_session",
            side_effect=RuntimeError("index delete failed"),
        ):
            result = document_service.batch_permanent_delete([doc_id])

        self.assertEqual({"success": 0, "failed": 1}, result)
        self.assertTrue(file_path.exists())
        with self.session() as session:
            self.assertIsNotNone(session.get(Document, doc_id))

    def test_shared_file_is_deleted_only_after_last_reference(self):
        file_path = self.data_dir / "documents" / "shared.pdf"
        file_path.parent.mkdir(parents=True)
        file_path.write_bytes(b"pdf")
        first_id = self.create_document("第一条")
        second_id = self.create_document("第二条")

        first_result = document_service.batch_permanent_delete([first_id])
        self.assertEqual({"success": 1, "failed": 0}, first_result)
        self.assertTrue(file_path.exists())

        second_result = document_service.batch_permanent_delete([second_id])
        self.assertEqual({"success": 1, "failed": 0}, second_result)
        self.assertFalse(file_path.exists())

    def test_absolute_and_relative_path_aliases_do_not_delete_shared_file(self):
        file_path = self.data_dir / "documents" / "aliased.pdf"
        file_path.parent.mkdir(parents=True)
        file_path.write_bytes(b"pdf")
        relative_id = self.create_document(
            "相对路径记录", file_path="documents/aliased.pdf"
        )
        absolute_id = self.create_document(
            "绝对路径记录", file_path=str(file_path)
        )

        first_result = document_service.batch_permanent_delete([relative_id])
        self.assertEqual({"success": 1, "failed": 0}, first_result)
        self.assertTrue(file_path.exists())

        second_result = document_service.batch_permanent_delete([absolute_id])
        self.assertEqual({"success": 1, "failed": 0}, second_result)
        self.assertFalse(file_path.exists())

    def test_missing_document_is_reported_as_failed(self):
        result = document_service.batch_permanent_delete([99999])
        self.assertEqual({"success": 0, "failed": 1}, result)

    def test_duplicate_id_does_not_decrement_tag_twice(self):
        with self.session() as session:
            tag = Tag(name="单次扣减", usage_count=1)
            session.add(tag)
            session.flush()
            tag_id = tag.id
        doc_id = self.create_document("重复删除", tag=tag_id)

        result = document_service.batch_permanent_delete([doc_id, doc_id])

        self.assertEqual({"success": 1, "failed": 1}, result)
        with self.session() as session:
            self.assertEqual(0, session.get(Tag, tag_id).usage_count)


if __name__ == "__main__":
    unittest.main()
