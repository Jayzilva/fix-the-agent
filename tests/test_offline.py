"""Offline checks - no API calls. Run: python -m unittest discover tests"""
import asyncio
import unittest
from unittest import mock

from app import llm, pipeline
from app.kb import article_ids, kb_index, keyword_search
from app.refund import check_refund


class RefundTests(unittest.TestCase):
    def test_unknown_customer_is_not_eligible(self):
        decision = check_refund("C9999", "2026-09-10")
        self.assertFalse(decision.found)
        self.assertFalse(decision.eligible)

    def test_windows(self):
        # T0002 in data/tickets.jsonl: starter_monthly, charged 4 days before the ticket.
        decision = check_refund("C0476", "2026-09-13")
        self.assertEqual(decision.plan_id, "starter_monthly")
        self.assertTrue(decision.eligible)
        self.assertEqual(decision.window_days, 14)


class KbTests(unittest.TestCase):
    def test_index_is_compact_and_complete(self):
        self.assertEqual(len(article_ids()), 60)
        self.assertLess(len(kb_index().split()), 4000)

    def test_search_returns_at_most_three(self):
        self.assertLessEqual(len(keyword_search("build timeout deploy")), 3)


class PipelineTests(unittest.TestCase):
    TICKET = {"ticket_id": "T9", "customer_id": "C0476", "created_at": "2026-09-13", "subject": "s", "body": "b"}

    def run_with(self, triage_result):
        async def fake_triage(ticket, refund):
            return dict(triage_result)

        with mock.patch.object(llm, "triage", fake_triage), \
                mock.patch.object(llm, "shorten_reply", side_effect=AssertionError("no model call expected")):
            return asyncio.run(pipeline.process_ticket(self.TICKET))

    def test_feature_request_drops_article(self):
        out = self.run_with({"category": "feature_request", "priority": "P3", "kb_article_id": "KB-001",
                             "reply_draft": "Thanks."})
        self.assertIsNone(out["kb_article_id"])
        self.assertTrue(out["refund_eligible"])

    def test_unknown_article_is_nulled_and_category_follows_article(self):
        out = self.run_with({"category": "technical", "priority": "P3", "kb_article_id": "KB-999",
                             "reply_draft": "Hi."})
        self.assertIsNone(out["kb_article_id"])
        out = self.run_with({"category": "technical", "priority": "P3", "kb_article_id": "KB-001",
                             "reply_draft": "Hi."})
        self.assertEqual(out["category"], "billing")

    def test_output_fields(self):
        out = self.run_with({"category": "other", "priority": "P3", "kb_article_id": None, "reply_draft": "Hi."})
        self.assertEqual(list(out), ["ticket_id", *pipeline.FIELDS])


if __name__ == "__main__":
    unittest.main()
