"""glossary.json 검사기.

1단계: JSON Schema로 모양을 검사한다 (칸 이름, 값 종류, 길이).
2단계: 스키마가 못 잡는 참조를 검사한다 (가리키는 용어가 실제로 있는지).

실행: python pipeline/validate.py
결과: 오류가 있으면 종료 코드 1 → GitHub Actions에서 배포가 멈춘다.
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "glossary.schema.json"
DATA_PATH = ROOT / "site" / "data" / "glossary.json"
SITE_DIR = ROOT / "site"


def check_schema(data, schema):
    """1단계: 스키마 검사. 오류 문장 목록을 돌려준다."""
    validator = Draft202012Validator(schema)
    errors = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "(맨 위)"
        errors.append(f"[스키마] {where}: {err.message}")
    return errors


def check_references(data):
    """2단계: 참조 검사. (오류 목록, 경고 목록)을 돌려준다."""
    errors, warnings = [], []
    terms = data.get("terms", [])

    # id 중복 검사
    seen = set()
    for t in terms:
        if t["id"] in seen:
            errors.append(f"[중복] 용어 id '{t['id']}'가 두 번 이상 있습니다.")
        seen.add(t["id"])

    for t in terms:
        # 같은 상황 예문이 두 번 있는지
        contexts = [ex["context"] for ex in t.get("examples", [])]
        if len(contexts) != len(set(contexts)):
            errors.append(f"[예문] '{t['id']}'에 같은 상황 예문이 두 번 있습니다: {contexts}")

        # related·prerequisites가 아직 없는 용어를 가리키는지 (경고: 시드가 늘면 생길 수 있음)
        for field, label in (("related", "관련"), ("prerequisites", "선수 지식")):
            for ref in t.get(field, []):
                if ref == t["id"]:
                    errors.append(f"[{label}] '{t['id']}'가 자기 자신을 가리킵니다.")
                elif ref not in seen:
                    warnings.append(f"[{label}] '{t['id']}' → '{ref}' 용어가 아직 없습니다.")

        # also_stages에 주 단계(stage)가 또 들어 있는지
        if t["stage"] in t.get("also_stages", []):
            errors.append(f"[단계] '{t['id']}'의 also_stages에 주 단계 '{t['stage']}'가 또 있습니다.")

        # replaced_by: 옮겨 간 용어가 실제로 있어야 한다 (오류). 복습 기록이 그쪽으로 옮겨지기 때문.
        if "replaced_by" in t:
            target = t["replaced_by"]
            if target == t["id"]:
                errors.append(f"[대체] '{t['id']}'가 자기 자신으로 대체되어 있습니다.")
            elif target not in seen:
                errors.append(f"[대체] '{t['id']}' → '{target}' 용어가 없습니다. 복습 기록이 갈 곳이 없어집니다.")

        # 그림 파일이 있는지 (경고)
        if "visual" in t and not (SITE_DIR / t["visual"]["file"]).exists():
            warnings.append(f"[그림] '{t['visual']['file']}' 파일이 아직 없습니다.")

    retired = {t["id"] for t in terms if "replaced_by" in t}
    pair_ids = set()
    for p in data.get("confusable_pairs", []):
        if p["id"] in pair_ids:
            errors.append(f"[중복] 혼동 쌍 id '{p['id']}'가 두 번 이상 있습니다.")
        pair_ids.add(p["id"])
        for side in ("a", "b"):
            if p[side] not in seen:
                errors.append(f"[혼동 쌍] '{p['id']}'의 {side}쪽 '{p[side]}' 용어가 없습니다.")
        if p["a"] == p["b"]:
            errors.append(f"[혼동 쌍] '{p['id']}'의 a와 b가 같습니다.")
        for side in ("a", "b"):
            if p[side] in retired:
                warnings.append(f"[혼동 쌍] '{p['id']}'가 대체된 용어 '{p[side]}'를 씁니다. 새 용어로 바꿔 주세요.")
        if "visual" in p and not (SITE_DIR / p["visual"]["file"]).exists():
            warnings.append(f"[그림] '{p['visual']['file']}' 파일이 아직 없습니다.")

    return errors, warnings


def main():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    errors = check_schema(data, schema)
    # 모양이 틀리면 참조 검사가 엉뚱하게 실패하므로, 스키마 통과 후에만 진행한다.
    warnings = []
    if not errors:
        ref_errors, warnings = check_references(data)
        errors += ref_errors

    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")

    n_terms = len(data.get("terms", []))
    n_pairs = len(data.get("confusable_pairs", []))
    if errors:
        print(f"\n실패: 오류 {len(errors)}개, 경고 {len(warnings)}개")
        sys.exit(1)
    print(f"\n통과: 용어 {n_terms}개, 혼동 쌍 {n_pairs}개 (경고 {len(warnings)}개)")


if __name__ == "__main__":
    main()
