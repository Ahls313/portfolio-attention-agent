import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from decision_log import log_decision, read_last, query


@pytest.fixture
def temp_journal(tmp_path):
    return str(tmp_path / "test_journal.jsonl")


class TestLogDecision:
    def test_writes_entry_with_expected_fields(self, temp_journal):
        entry = log_decision("watch_agent", "BTC", "no_act",
                              reasons=["score below threshold"],
                              path=temp_journal, score=41.0)
        assert entry["symbol"] == "BTC"
        assert entry["decision"] == "no_act"
        assert entry["score"] == 41.0
        assert "ts" in entry
        assert "run_id" in entry

    def test_appends_without_overwriting(self, temp_journal):
        log_decision("watch_agent", "BTC", "no_act", path=temp_journal)
        log_decision("watch_agent", "ETH", "act", path=temp_journal)
        entries = read_last(10, path=temp_journal)
        assert len(entries) == 2


class TestReadLast:
    def test_returns_empty_list_when_file_missing(self, temp_journal):
        assert read_last(5, path=temp_journal) == []

    def test_respects_n_limit_and_ordering(self, temp_journal):
        for i in range(5):
            log_decision("watch_agent", "BTC", "no_act", path=temp_journal, seq=i)
        last_two = read_last(2, path=temp_journal)
        assert len(last_two) == 2
        assert last_two[-1]["seq"] == 4  # most recent last


class TestQuery:
    def test_filters_by_predicate(self, temp_journal):
        log_decision("watch_agent", "BTC", "no_act", path=temp_journal)
        log_decision("watch_agent", "ETH", "act", path=temp_journal)
        log_decision("watch_agent", "BTC", "no_act", path=temp_journal)

        acted = query(lambda e: e["decision"] == "act", path=temp_journal)
        assert len(acted) == 1
        assert acted[0]["symbol"] == "ETH"

        btc_holds = query(lambda e: e["symbol"] == "BTC" and e["decision"] == "no_act",
                           path=temp_journal)
        assert len(btc_holds) == 2

    def test_returns_empty_list_when_file_missing(self, temp_journal):
        assert query(lambda e: True, path=temp_journal) == []