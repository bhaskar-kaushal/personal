"""
Unit tests for genaibootcampassign3 (basic-rag and conversational-rag).
Run from repo root: python -m unittest tests.test
Requires: pip install -r requirements.txt in basic-rag and conversational-rag (or repo deps).
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "basic-rag"))
sys.path.insert(0, str(REPO_ROOT / "conversational-rag"))

# basic-rag: extract_content has pure helpers
from extract_content import chunk_text, clean_text

# conversational-rag: message_trimming
from message_trimming import count_tokens, get_encoding, trim_messages


class TestChunkText(unittest.TestCase):
    """Tests for extract_content.chunk_text."""

    def test_empty_or_whitespace_returns_empty_list(self):
        self.assertEqual(chunk_text(""), [])
        self.assertEqual(chunk_text("   "), [])

    def test_short_text_returns_single_chunk(self):
        text = "Short piece of text."
        self.assertEqual(chunk_text(text, chunk_size=1000), [text])

    def test_long_text_produces_multiple_chunks(self):
        text = "a" * 2500
        chunks = chunk_text(text, chunk_size=1000, overlap=200)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(isinstance(c, str) for c in chunks))

    def test_chunks_have_overlap_effect(self):
        text = "x" * 1500
        chunks = chunk_text(text, chunk_size=500, overlap=100)
        self.assertGreaterEqual(len(chunks), 2)


class TestCleanText(unittest.TestCase):
    """Tests for extract_content.clean_text."""

    def test_empty_returns_empty(self):
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")

    def test_normalizes_whitespace(self):
        result = clean_text("  hello   world  \n\n  ")
        self.assertEqual(result, "hello world")

    def test_strips_result(self):
        result = clean_text("  text  ")
        self.assertEqual(result, "text")


@unittest.skipUnless(
    (REPO_ROOT / "basic-rag" / "basic_rag.py").exists(),
    "basic-rag module not found",
)
class TestBasicRAGLoadDocuments(unittest.TestCase):
    """Tests for BasicRAG.load_documents using temp chunks.json."""

    def test_load_documents_reads_chunks_json(self):
        try:
            from basic_rag import BasicRAG
            from langchain_core.documents import Document
        except ImportError:
            self.skipTest("basic_rag dependencies (langchain, etc.) not installed")
        with tempfile.TemporaryDirectory() as tmpdir:
            chunks_path = Path(tmpdir) / "chunks.json"
            chunks_data = [
                {"content": "First chunk.", "metadata": {"source": "a"}},
                {"content": "Second chunk.", "metadata": {"source": "b"}},
            ]
            chunks_path.write_text(json.dumps(chunks_data), encoding="utf-8")
            rag = BasicRAG(content_dir=tmpdir)
            docs = rag.load_documents(content_dir=tmpdir)
            self.assertEqual(len(docs), 2)
            self.assertIsInstance(docs[0], Document)
            self.assertEqual(docs[0].page_content, "First chunk.")
            self.assertEqual(docs[1].page_content, "Second chunk.")

    def test_load_documents_missing_file_raises(self):
        try:
            from basic_rag import BasicRAG
        except ImportError:
            self.skipTest("basic_rag dependencies not installed")
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = BasicRAG(content_dir=tmpdir)
            with self.assertRaises(FileNotFoundError):
                rag.load_documents(content_dir=tmpdir)

    def test_load_documents_empty_json_returns_empty_list(self):
        try:
            from basic_rag import BasicRAG
        except ImportError:
            self.skipTest("basic_rag dependencies not installed")
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "chunks.json").write_text("[]", encoding="utf-8")
            rag = BasicRAG(content_dir=tmpdir)
            docs = rag.load_documents(content_dir=tmpdir)
            self.assertEqual(docs, [])


class TestMessageTrimming(unittest.TestCase):
    """Tests for message_trimming (conversational-rag)."""

    def test_get_encoding_returns_encoding(self):
        enc = get_encoding()
        self.assertTrue(hasattr(enc, "encode"))

    def test_count_tokens_empty_messages(self):
        self.assertEqual(count_tokens([]), 0)

    def test_count_tokens_single_message(self):
        messages = [{"role": "user", "content": "hello"}]
        n = count_tokens(messages)
        self.assertIsInstance(n, int)
        self.assertGreater(n, 0)

    def test_trim_messages_returns_tuple(self):
        messages = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]
        trimmed, total = trim_messages(messages, max_history_length=10)
        self.assertIsInstance(trimmed, list)
        self.assertIsInstance(total, int)
        self.assertEqual(len(trimmed), 2)
        self.assertEqual(trimmed[0]["content"], "Hi")
        self.assertEqual(trimmed[1]["content"], "Hello")

    def test_trim_messages_truncates_long_history(self):
        messages = []
        for i in range(20):
            messages.append({"role": "user", "content": f"Q{i}"})
            messages.append({"role": "assistant", "content": f"A{i}"})
        trimmed, _ = trim_messages(messages, max_history_length=3)
        self.assertLessEqual(len(trimmed), 6 + 1)  # 3 pairs + maybe summary


if __name__ == "__main__":
    unittest.main()
