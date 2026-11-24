"""AI 답 검수 문제(glossary.json의 ai_checks[]) 도구 모음.

요구: docs/requirements.md (AC-10 · 11 · 14 · 15 · 16 · 17), 설계: docs/data-model.md 결정 12~15, docs/flows.md 8-3.

- candidate_errors(): 후보 하나에 빠진 것이 있으면 오류 목록. 오류가 있으면 미리보기·승인 대기열에 올리지 않는다
- recheck_date(): 다시 확인할 날 계산 (최신 정보 +6개월, 나머지 +1년)
- check_refs(): validate.py가 부르는 참조 검사
- due_for_recheck(): 다시 확인할 날이 지난 문제 (주간 점검 보고서)
- add_checks() / mark_ok() / retire(): glossary.json의 ai_checks 부분만 다시 쓴다
"""
import calendar
import json
import re
from datetime import date

TYPES = ("number", "recency", "fact", "code")
TYPE_KO = {"number": "숫자", "recency": "최신 정보", "fact": "출처/사실", "code": "코드"}
RECHECK_MONTHS = {"recency": 6}          # AC-15
DEFAULT_RECHECK_MONTHS = 12              # AC-16
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DAY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
ORDER = ["id", "type", "prompt", "statements", "wrong", "correction", "how_to_check", "calc", "sources",
         "checked_at", "recheck_at", "terms", "retired_at", "created_at", "updated_at"]
ANCHOR = ',\n  "ai_checks": ['


def add_months(day: str, months: int) -> str:
    y, m, d = (int(x) for x in day.split("-"))
    m0 = m - 1 + months
    y, m = y + m0 // 12, m0 % 12 + 1
    d = min(d, calendar.monthrange(y, m)[1])   # 8월 31일 + 6개월 → 2월 28/29일
    return f"{y:04d}-{m:02d}-{d:02d}"


def recheck_date(kind: str, checked_at: str) -> str:
    return add_months(checked_at, RECHECK_MONTHS.get(kind, DEFAULT_RECHECK_MONTHS))


def candidate_errors(item: dict, term_ids: set) -> list:
    """후보 하나를 검사한다. 빈 목록이면 통과 (AC-10 · AC-11 + 모양)."""
    cid = item.get("id", "(id 없음)")
    errs = []
    if not SLUG.match(str(item.get("id", ""))):
        errs.append(f"[AI 답 검수] '{cid}': id는 영어 소문자·숫자·하이픈이어야 합니다")
    kind = item.get("type")
    if kind not in TYPES:
        errs.append(f"[AI 답 검수] '{cid}': type은 {', '.join(TYPES)} 중 하나여야 합니다")
    st = item.get("statements")
    if not isinstance(st, list) or len(st) != 3 or not all(isinstance(s, str) and s.strip() for s in st):
        errs.append(f"[AI 답 검수] '{cid}': AI 답 문장(statements)은 정확히 3개여야 합니다")
    if item.get("wrong") not in (0, 1, 2):
        errs.append(f"[AI 답 검수] '{cid}': 틀린 문장 번호(wrong)는 0·1·2 중 하나여야 합니다")
    for f, label in (("prompt", "질문"), ("correction", "바른 내용"), ("how_to_check", "확인 방법")):
        if not str(item.get(f, "")).strip():
            errs.append(f"[AI 답 검수] '{cid}': {label}({f})이 없습니다")
    # AC-10: 공식 출처 링크와 확인한 날짜
    sources = item.get("sources") or []
    good = [s for s in sources if str(s.get("url", "")).startswith("https://") and DAY.match(str(s.get("checked_at", "")))]
    if not good:
        errs.append(f"[AI 답 검수] '{cid}': 공식 출처 링크(https)와 확인한 날짜가 있는 출처가 1개 이상 필요합니다")
    if not DAY.match(str(item.get("checked_at", ""))):
        errs.append(f"[AI 답 검수] '{cid}': 사람이 확인한 날짜(checked_at)가 없습니다")
    # AC-11: 숫자 유형은 계산식
    if kind == "number" and not str(item.get("calc", "")).strip():
        errs.append(f"[AI 답 검수] '{cid}': 숫자 유형은 계산식(calc)이 필요합니다")
    # AS-4: 관련 용어 1개 이상, 실제 있는 용어
    terms = item.get("terms") or []
    if not terms:
        errs.append(f"[AI 답 검수] '{cid}': 관련 용어(terms)가 1개 이상 필요합니다")
    for t in terms:
        if t not in term_ids:
            errs.append(f"[AI 답 검수] '{cid}': 관련 용어 '{t}'가 없습니다")
    return errs


def check_refs(data: dict) -> list:
    """validate.py 2단계에서 부른다. 공개 파일의 ai_checks 참조 검사."""
    term_ids = {t["id"] for t in data.get("terms", [])}
    errs, seen = [], set()
    for item in data.get("ai_checks", []):
        if item["id"] in seen:
            errs.append(f"[중복] AI 답 검수 id '{item['id']}'가 두 번 이상 있습니다.")
        seen.add(item["id"])
        errs += candidate_errors(item, term_ids)
        want = recheck_date(item["type"], item["checked_at"])
        if item.get("recheck_at") != want:
            errs.append(f"[AI 답 검수] '{item['id']}': 다시 확인할 날이 {item.get('recheck_at')}인데 규칙상 {want}여야 합니다")
    return errs


def due_for_recheck(data: dict, today: str) -> list:
    """다시 확인할 날이 지난(오늘 포함) 공개 문제. 내린 문제는 뺀다 (AC-13 · AC-14)."""
    return [c for c in data.get("ai_checks", []) if not c.get("retired_at") and c["recheck_at"] <= today]


# ---------- glossary.json의 ai_checks 부분 읽고 쓰기 ----------

def split(raw: str):
    """(ai_checks 앞부분, ai_checks 목록). 앞부분은 '\n}'로 끝나지 않은 채로 돌려준다."""
    if ANCHOR in raw:
        head = raw[: raw.index(ANCHOR)]
        checks = json.loads(raw)["ai_checks"]
    else:
        body = raw.rstrip()
        if not body.endswith("\n}"):
            raise SystemExit("glossary.json 끝 모양을 알 수 없습니다.")
        head, checks = body[:-2], []
    return head, checks


def _item_text(c: dict) -> str:
    keys = [k for k in ORDER if k in c] + [k for k in c if k not in ORDER]
    lines = []
    for k in keys:
        v = c[k]
        if k == "statements":
            inner = ",\n".join(f"        {json.dumps(s, ensure_ascii=False)}" for s in v)
            lines.append(f'      "statements": [\n{inner}\n      ]')
        elif k == "sources":
            inner = ",\n".join("        { " + ", ".join(f"{json.dumps(a, ensure_ascii=False)}: {json.dumps(b, ensure_ascii=False)}" for a, b in s.items()) + " }" for s in v)
            lines.append(f'      "sources": [\n{inner}\n      ]')
        else:
            lines.append(f"      {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}")
    return "    {\n" + ",\n".join(lines) + "\n    }"


def join(head: str, checks: list) -> str:
    body = ",\n".join(_item_text(c) for c in checks)
    return head + ANCHOR + ("\n" + body + "\n  " if checks else "") + "]\n}\n"


def set_version(raw: str, version: str = "1.2") -> str:
    return re.sub(r'"schema_version": "[0-9.]+"', f'"schema_version": "{version}"', raw, count=1)


def add_checks(raw: str, items: list, today: str) -> str:
    """승인한 후보를 넣는다. 다시 확인할 날을 계산해 넣는다 (AC-15 · 16). 오류가 있으면 멈춘다 (AC-10 · 11)."""
    data = json.loads(raw)
    term_ids = {t["id"] for t in data["terms"]}
    have = {c["id"] for c in data.get("ai_checks", [])}
    errs = []
    for it in items:
        errs += candidate_errors(it, term_ids)
        if it.get("id") in have:
            errs.append(f"[AI 답 검수] '{it['id']}': 이미 있는 id입니다")
    if errs:
        raise SystemExit("AI 답 검수 후보에 빠진 것이 있어 넣지 않습니다:\n" + "\n".join(errs))
    head, checks = split(raw)
    for it in items:
        c = {k: v for k, v in it.items() if v is not None}   # 빈 칸은 넣지 않는다
        c["recheck_at"] = recheck_date(c["type"], c["checked_at"])
        c.setdefault("created_at", today)
        c["updated_at"] = today
        checks.append(c)
    out = set_version(join(head, checks))
    json.loads(out)
    return out


def _change(raw: str, cid: str, fn) -> str:
    head, checks = split(raw)
    hit = [c for c in checks if c["id"] == cid]
    if not hit:
        raise SystemExit(f"AI 답 검수 문제 '{cid}'가 없습니다.")
    fn(hit[0])
    out = join(head, checks)
    json.loads(out)
    return out


def mark_ok(raw: str, cid: str, today: str) -> str:
    """'다시 확인함' (AC-17): 확인일 = 오늘, 다시 확인할 날 다시 계산."""
    def fn(c):
        c["checked_at"] = today
        c["recheck_at"] = recheck_date(c["type"], today)
        c["updated_at"] = today
    return _change(raw, cid, fn)


def retire(raw: str, cid: str, today: str) -> str:
    """'내리기' (AC-17): 지우지 않고 내린 날을 적는다. 사이트가 목록·링크에서 뺀다."""
    def fn(c):
        c["retired_at"] = today
        c["updated_at"] = today
    return _change(raw, cid, fn)


def today_str() -> str:
    return date.today().isoformat()
