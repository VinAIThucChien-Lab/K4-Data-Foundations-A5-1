import unittest
from unittest.mock import patch

from src.demo_chunkers import SonCustomChunker
from web_app import STRATEGIES, build_chunker, chunk_payload, corpus_documents, runtime_status


class TestSonCustomChunker(unittest.TestCase):
    def test_splits_numbered_policy_sections(self):
        text = "1. Điều kiện\nNội dung một.\n\n2. Thời hạn\nNội dung hai."
        chunks = SonCustomChunker(max_chunk_size=100, min_chunk_size=0).chunk(text)
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0].startswith("1."))
        self.assertTrue(chunks[1].startswith("2."))

    def test_falls_back_for_unstructured_text(self):
        chunks = SonCustomChunker(max_chunk_size=10, min_chunk_size=0).chunk("abcdefghij klmnopqrst")
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 10 for chunk in chunks))


class TestChunkLabApiLogic(unittest.TestCase):
    def test_builds_every_supported_method(self):
        for method in ("fixed", "sentence", "recursive", "custom"):
            self.assertIsNotNone(build_chunker(method, {}))

    def test_api_strategy_catalog_is_complete(self):
        self.assertEqual(
            {item["id"] for item in STRATEGIES},
            {"fixed", "sentence", "recursive", "custom"},
        )

    def test_structured_alias_remains_supported(self):
        self.assertIsNotNone(build_chunker("structured", {}))

    def test_payload_contains_stats_and_chunks(self):
        result = chunk_payload("Một câu. Hai câu. Ba câu.", "sentence", {"sentences": 2})
        self.assertEqual(result["stats"]["count"], 2)
        self.assertEqual(len(result["chunks"]), 2)
        self.assertIn("average", result["stats"])

    def test_corpus_only_exposes_real_shopee_documents(self):
        docs = corpus_documents()
        self.assertTrue(all(doc["id"].startswith("shopee-returns-") for doc in docs))

    def test_runtime_status_reports_key_without_exposing_it(self):
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "secret-test-key", "OPENAI_EMBEDDING_MODEL": "test-model"},
        ):
            status = runtime_status()
        self.assertTrue(status["api_key_configured"])
        self.assertEqual(status["mode"], "openai")
        self.assertEqual(status["embedding_model"], "test-model")
        self.assertNotIn("secret-test-key", repr(status))


if __name__ == "__main__":
    unittest.main()
