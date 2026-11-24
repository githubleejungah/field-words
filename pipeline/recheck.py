"""AI 답 검수 문제 다시 확인하기 (요구 AC-17). 주간 점검 보고서의 "다시 확인" 목록을 보고 사람이 실행한다.

사용법
  python pipeline/recheck.py <문제 id> --ok       # 공식 출처로 다시 확인함 → 확인일 = 오늘, 다시 확인할 날 다시 계산
  python pipeline/recheck.py <문제 id> --retire   # 내리기 → retired_at = 오늘 (지우지 않음, 사이트가 보여 주지 않음)

- 검사를 통과하지 못하면 원래대로 되돌린다. 커밋은 사람이 한다.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import aicheck   # noqa: E402
import promote   # noqa: E402
import seedlib   # noqa: E402


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ok, retire = "--ok" in sys.argv, "--retire" in sys.argv
    if len(args) != 1 or ok == retire:
        sys.exit(__doc__)
    cid, today = args[0], aicheck.today_str()
    original = seedlib.PATH.read_text(encoding="utf-8")
    raw = aicheck.mark_ok(original, cid, today) if ok else aicheck.retire(original, cid, today)
    seedlib.PATH.write_text(raw, encoding="utf-8", newline="\n")
    errors, _, _ = promote.check(seedlib.PATH)
    if errors:
        seedlib.PATH.write_text(original, encoding="utf-8", newline="\n")
        sys.exit("검사 오류가 있어 되돌렸습니다:\n" + "\n".join(errors))
    print(f"✅ '{cid}' {'다시 확인함 (확인일 ' + today + ')' if ok else '내림 (' + today + ')'}. 앱에서 확인한 뒤 커밋하세요.")


if __name__ == "__main__":
    main()
