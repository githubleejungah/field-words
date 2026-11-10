"""시드 용어를 glossary.json에 기존 파일 모양 그대로 추가하는 도구.

사용법 (다른 스크립트에서):
    from seedlib import ex, src, add
    add(TERMS, PAIRS)

- 이미 있는 id는 추가하지 않고 멈춘다 (덮어쓰기 방지)
- 추가한 뒤 올바른 JSON인지 확인하고 저장한다
- 내용 검사는 따로 pipeline/validate.py로 한다
"""
import json
import sys
from datetime import date
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "site" / "data" / "glossary.json"
TODAY = date.today().isoformat()

ORDER = ["id", "term_en", "term_ko", "aliases", "expansion", "expansion_ko", "pronunciation", "stage", "also_stages",
         "level", "definition", "analogy", "pitfall", "interview_q", "interview_a", "examples", "tags", "related",
         "prerequisites", "sources"]
CHECK = {"decided_by": "claude", "judged_by": "claude 자체 검토 (별도 프롬프트 검사 전)"}


def ex(*pairs):
    """("meeting", "예문") 쌍들을 예문 목록으로"""
    return [{"context": c, "sentence": s} for c, s in pairs]


def src(kind, label, when=None):
    return [{"type": kind, "label": label, "date": when or TODAY}]


def _j(v):
    return json.dumps(v, ensure_ascii=False)


def _inline(obj):
    return "{ " + ", ".join(f"{_j(k)}: {_j(v)}" for k, v in obj.items()) + " }"


def term_text(t):
    lines = []
    for k in ORDER:
        if k not in t:
            continue
        if k == "examples":
            inner = ",\n".join(f'        {{ "context": {_j(e["context"])}, "sentence": {_j(e["sentence"])} }}' for e in t[k])
            lines.append(f'      "examples": [\n{inner}\n      ]')
        elif k == "pronunciation":
            lines.append(f'      "pronunciation": {_inline(t[k])}')
        elif k == "sources":
            lines.append('      "sources": [' + ", ".join(_inline(x) for x in t[k]) + "]")
        else:
            lines.append(f"      {_j(k)}: {_j(t[k])}")
    lines += [f'      "created_at": "{TODAY}"', f'      "updated_at": "{TODAY}"']
    return "    {\n" + ",\n".join(lines) + "\n    }"


def pair_text(p):
    check = _inline({**CHECK, "judged_at": TODAY})
    return ("    {\n"
            f'      "id": {_j(p["id"])},\n      "a": {_j(p["a"])},\n      "b": {_j(p["b"])},\n'
            f'      "difference": {_j(p["difference"])},\n      "check": {check}\n'
            "    }")


def add(terms, pairs=()):
    sys.stdout.reconfigure(encoding="utf-8")
    raw = PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    have_terms = {t["id"] for t in data["terms"]}
    have_pairs = {p["id"] for p in data["confusable_pairs"]}
    dup = [t["id"] for t in terms if t["id"] in have_terms] + [p["id"] for p in pairs if p["id"] in have_pairs]
    if dup:
        sys.exit(f"이미 있는 id라서 멈춥니다: {dup}")

    anchor = '    }\n  ],\n  "confusable_pairs": ['
    if raw.count(anchor) != 1:
        sys.exit("용어 목록의 끝을 찾지 못했습니다. 파일 모양이 바뀌었는지 확인하세요.")
    if terms:
        raw = raw.replace(anchor, "    },\n" + ",\n".join(term_text(t) for t in terms) + '\n  ],\n  "confusable_pairs": [')

    if pairs:
        end = "    }\n  ]\n}"
        body = raw.rstrip()
        if not body.endswith(end):
            sys.exit("혼동 쌍 목록의 끝을 찾지 못했습니다.")
        raw = body[: -len(end)] + "    },\n" + ",\n".join(pair_text(p) for p in pairs) + "\n  ]\n}\n"

    json.loads(raw)  # 올바른 JSON인지 확인
    PATH.write_text(raw, encoding="utf-8", newline="\n")
    print(f"추가: 용어 {len(terms)}개, 혼동 쌍 {len(pairs)}개")
