"""AI 답 검수 파이프라인 시험 (요구 docs/requirements.md AC-10 · 11 · 14 · 15 · 16 · 17).

실행: python -m unittest discover -s tests -p "test_*.py"
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import aicheck  # noqa: E402

TERMS = {"rate-limit", "cache"}


def good(**over):
    c = {
        "id": "rate-limit-per-second", "type": "number",
        "prompt": "호출 한도를 어떻게 잡아야 하나요?",
        "statements": ["하루 1,200,000건이면 초당 약 140건이에요.", "한도를 넘으면 보통 429를 돌려줘요.", "Retry-After로 다시 보낼 시점을 알려 줄 수 있어요."],
        "wrong": 0, "correction": "초당 약 14건입니다.", "how_to_check": "하루 = 86,400초로 직접 나눠 보기",
        "calc": "1,200,000 ÷ 86,400 ≈ 13.9",
        "sources": [{"label": "MDN 429", "url": "https://developer.mozilla.org/docs/Web/HTTP/Status/429", "checked_at": "2026-11-24"}],
        "checked_at": "2026-11-24", "terms": ["rate-limit"],
    }
    c.update(over)
    return c


def base_raw():
    return json.dumps({"schema_version": "1.1", "updated_at": "2026-11-24",
                       "terms": [{"id": t} for t in sorted(TERMS)], "confusable_pairs": []},
                      ensure_ascii=False, indent=2) + "\n"


class CandidateCheck(unittest.TestCase):
    def test_good_candidate_passes(self):
        self.assertEqual(aicheck.candidate_errors(good(), TERMS), [])

    def test_ac10_no_source_link_blocked(self):
        self.assertTrue(aicheck.candidate_errors(good(sources=[]), TERMS))
        self.assertTrue(aicheck.candidate_errors(good(sources=[{"label": "x", "url": "http://a", "checked_at": "2026-11-24"}]), TERMS))

    def test_ac10_no_checked_date_blocked(self):
        c = good(); del c["checked_at"]
        self.assertTrue(aicheck.candidate_errors(c, TERMS))
        self.assertTrue(aicheck.candidate_errors(good(sources=[{"label": "x", "url": "https://a"}]), TERMS))

    def test_ac11_number_without_calc_blocked(self):
        c = good(); del c["calc"]
        self.assertTrue(any("계산식" in e for e in aicheck.candidate_errors(c, TERMS)))
        c2 = good(type="fact"); del c2["calc"]
        self.assertEqual(aicheck.candidate_errors(c2, TERMS), [])     # 숫자 유형이 아니면 계산식 없어도 됨

    def test_shape_three_statements_one_wrong(self):
        self.assertTrue(aicheck.candidate_errors(good(statements=["a 문장입니다", "b 문장입니다"]), TERMS))
        self.assertTrue(aicheck.candidate_errors(good(wrong=3), TERMS))
        self.assertTrue(aicheck.candidate_errors(good(terms=["no-such-term"]), TERMS))

    def test_ac10_ac11_add_refuses_whole_batch(self):
        with self.assertRaises(SystemExit):
            aicheck.add_checks(base_raw(), [good(), good(id="b", sources=[])], "2026-11-24")


class RecheckDate(unittest.TestCase):
    def test_ac15_recency_six_months(self):
        self.assertEqual(aicheck.recheck_date("recency", "2026-11-24"), "2027-05-24")

    def test_ac16_others_one_year(self):
        for k in ("number", "fact", "code"):
            self.assertEqual(aicheck.recheck_date(k, "2026-11-24"), "2027-11-24")

    def test_month_end(self):
        self.assertEqual(aicheck.recheck_date("recency", "2026-08-31"), "2027-02-28")


class WriteAndRecheck(unittest.TestCase):
    def setUp(self):
        self.raw = aicheck.add_checks(base_raw(), [good(), good(id="py2-eol", type="recency", calc=None)], "2026-11-24")

    def data(self, raw=None):
        return json.loads(raw or self.raw)

    def test_add_sets_recheck_and_version(self):
        d = self.data()
        self.assertEqual(d["schema_version"], "1.2")
        by = {c["id"]: c for c in d["ai_checks"]}
        self.assertEqual(by["rate-limit-per-second"]["recheck_at"], "2027-11-24")
        self.assertEqual(by["py2-eol"]["recheck_at"], "2027-05-24")
        self.assertEqual(aicheck.check_refs(d), [])

    def test_ac14_due_list(self):
        d = self.data()
        self.assertEqual(aicheck.due_for_recheck(d, "2027-05-23"), [])
        self.assertEqual([c["id"] for c in aicheck.due_for_recheck(d, "2027-05-24")], ["py2-eol"])

    def test_ac17_ok_moves_dates(self):
        d = self.data(aicheck.mark_ok(self.raw, "py2-eol", "2027-06-01"))
        c = {c["id"]: c for c in d["ai_checks"]}["py2-eol"]
        self.assertEqual((c["checked_at"], c["recheck_at"]), ("2027-06-01", "2027-12-01"))
        self.assertEqual(aicheck.due_for_recheck(d, "2027-06-02"), [])

    def test_ac17_retire_keeps_item_and_hides_from_due(self):
        d = self.data(aicheck.retire(self.raw, "py2-eol", "2027-06-01"))
        ids = [c["id"] for c in d["ai_checks"]]
        self.assertIn("py2-eol", ids)                           # 지우지 않는다 (D-6)
        self.assertEqual(aicheck.due_for_recheck(d, "2030-01-01")[0]["id"], "rate-limit-per-second")
        self.assertEqual(len(aicheck.due_for_recheck(d, "2030-01-01")), 1)

    def test_refs_catch_wrong_recheck_rule(self):
        d = self.data()
        d["ai_checks"][0]["recheck_at"] = "2099-01-01"
        self.assertTrue(aicheck.check_refs(d))


if __name__ == "__main__":
    unittest.main()
