"""승인 대기 후보 묶음을 공개 데이터(glossary.json)에 넣는다. 사람이 검토하고 승인한 뒤에만 실행한다.

사용법
  python pipeline/promote.py pipeline/candidates/2026-11-16.py --dry-run   # 임시 복사본에 넣어 검사만 (원본 그대로)
  python pipeline/promote.py pipeline/candidates/2026-11-16.py             # 실제로 추가 (승인 후)

실제로 추가할 때
  - 넣기 전 원본을 기억해 두고, 검사에서 오류가 나면 원래대로 되돌린다
  - 성공하면 후보 파일을 pipeline/seeds/ 로 옮겨 기록으로 남긴다 (Git에 올라감)
  - 커밋은 하지 않는다. 사람이 확인하고 커밋한다
"""
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PIPELINE = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPELINE))
import seedlib   # noqa: E402
import validate  # noqa: E402


def load_batch(path):
    spec = importlib.util.spec_from_file_location("candidate_batch", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)   # 후보 파일은 `if __name__ == "__main__"`일 때만 추가하므로 불러오기만 해도 안전
    return module.TERMS, getattr(module, "PAIRS", [])


def check(data_path):
    schema = json.loads(validate.SCHEMA_PATH.read_text(encoding="utf-8"))
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    errors = validate.check_schema(data, schema)
    warnings = []
    if not errors:
        ref_errors, warnings = validate.check_references(data)
        errors += ref_errors
    return errors, warnings, data


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if not args:
        sys.exit(__doc__)
    batch = Path(args[0]).resolve()
    terms, pairs = load_batch(batch)
    print(f"후보: 용어 {len(terms)}개, 혼동 쌍 {len(pairs)}개 ({batch.name})")

    if dry:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "glossary.json"
            shutil.copy(seedlib.PATH, copy)
            seedlib.PATH = copy
            seedlib.add(terms, pairs)
            errors, warnings, data = check(copy)
        for w in warnings:
            print(f"⚠️  {w}")
        for e in errors:
            print(f"❌ {e}")
        print(f"\n[검사만] {'실패' if errors else '통과'}: 넣으면 용어 {len(data['terms'])}개가 됩니다. 원본은 바뀌지 않았습니다.")
        sys.exit(1 if errors else 0)

    original = seedlib.PATH.read_text(encoding="utf-8")
    seedlib.add(terms, pairs)
    errors, warnings, data = check(seedlib.PATH)
    if errors:
        seedlib.PATH.write_text(original, encoding="utf-8", newline="\n")
        for e in errors:
            print(f"❌ {e}")
        sys.exit("검사 오류가 있어 원래대로 되돌렸습니다. 후보 파일을 고친 뒤 다시 실행하세요.")

    target = PIPELINE / "seeds" / f"batch_{batch.stem}.py"
    shutil.move(str(batch), target)
    for w in warnings:
        print(f"⚠️  {w}")
    print(f"✅ 추가 완료: 용어 {len(data['terms'])}개. 후보 파일은 {target.relative_to(PIPELINE.parent)} 로 옮겼습니다. 앱에서 확인한 뒤 커밋하세요.")


if __name__ == "__main__":
    main()
