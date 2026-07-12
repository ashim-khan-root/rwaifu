import sys, json, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from db import init_db
init_db()
import insight_ledger


class TestInsightLedger:
    def test_log_and_query(self):
        count_before = len(insight_ledger.query_insights(limit=0))
        insight_ledger.log_insight("test_event", {"key": "val"})
        results = insight_ledger.query_insights(event="test_event")
        assert len(results) >= 1
        assert results[0]["event"] == "test_event"
        assert results[0]["payload"]["key"] == "val"

    def test_query_limit(self):
        results = insight_ledger.query_insights(limit=2)
        assert len(results) <= 2

    def test_query_since(self):
        today = datetime.date.today().isoformat()
        results = insight_ledger.query_insights(since=today)
        assert all(r.get("timestamp", "").startswith(today) or r.get("timestamp", "") >= today for r in results)

    def test_get_stats(self):
        stats = insight_ledger.get_stats()
        assert "total" in stats
        assert "event_types" in stats
        assert stats["total"] >= 0

    def test_log_no_payload(self):
        insight_ledger.log_insight("test_no_payload")
        results = insight_ledger.query_insights(event="test_no_payload")
        assert len(results) >= 1
        assert results[0]["payload"] == {}
