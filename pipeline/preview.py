"""후보 묶음을 사람이 읽기 쉬운 미리보기(.md)로 만든다. 승인 전에 내용을 확인하는 용도.

사용법
  python pipeline/preview.py pipeline/candidates/2026-11-13_서버인프라.py
  → 같은 폴더에 2026-11-13_서버인프라_미리보기.md 가 생긴다 (pipeline/candidates/ 는 Git에 올리지 않음)
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from promote import load_batch  # noqa: E402

STAGE = {"discovery": "① 발견·기획", "design": "② 설계", "build": "③ 개발", "test": "④ 테스트·품질", "deploy": "⑤ 배포",
         "operate": "⑥ 운영", "secure": "⑦ 보안·개인정보", "grow": "⑧ 개선·확장", "automate": "⑨ 자동화·지속 개선"}
LEVEL = {1: "입문", 2: "기본", 3: "실무", 4: "심화"}
CONTEXT = {"meeting": "업무 회의", "interview": "면접 답변", "review": "문서·코드 리뷰"}


def render(terms, pairs, name):
    out = [f"# 미리보기: {name}", "", f"- 용어 {len(terms)}개, 헷갈리기 쉬운 짝 {len(pairs)}개",
           "- 고칠 것이 있으면 '용어 이름 → 고칠 내용'으로 알려 주세요.", ""]
    out += ["## 한눈에 보기", "", "| # | 용어 | 단계 · 등급 | 한 줄 뜻 |", "|---|---|---|---|"]
    for i, t in enumerate(terms, 1):
        first = t["definition"].split(". ")[0].rstrip(".") + "."
        out.append(f"| {i} | **{t['term_en']}** {t['term_ko']} | {STAGE[t['stage']]} · {LEVEL[t['level']]} | {first} |")
    out.append("")
    for i, t in enumerate(terms, 1):
        p = t["pronunciation"]
        out += [f"## {i}. {t['term_en']} · {t['term_ko']}", "",
                f"- **발음**: {'/' + p['ipa'] + '/ · ' if p.get('ipa') else ''}현업 발음 {p['ko']}" + (f" ({p['note']})" if p.get("note") else ""),
                f"- **단계 · 등급**: {STAGE[t['stage']]} · {LEVEL[t['level']]}"]
        if t.get("expansion"):
            out.append(f"- **풀어 쓰기**: {t['expansion']} → {t.get('expansion_ko', '')}")
        out += ["", f"**뜻** {t['definition']}", ""]
        if t.get("analogy"):
            out += [f"**비유** {t['analogy']}", ""]
        out.append("**이렇게 써요**")
        out += [f"- ({CONTEXT[e['context']]}) {e['sentence']}" for e in t["examples"]]
        out.append("")
        if t.get("pitfall"):
            out += [f"**현업 함정** {t['pitfall']}", ""]
        if t.get("interview_q"):
            out += [f"**면접 질문** {t['interview_q']}", "", f"> **30초 모범 답변** {t['interview_a']}", ""]
    if pairs:
        out += ["## 헷갈리기 쉬운 짝", ""]
        by_id = {t["id"]: t["term_en"] for t in terms}
        for pr in pairs:
            out.append(f"- **{by_id.get(pr['a'], pr['a'])} ↔ {by_id.get(pr['b'], pr['b'])}**: {pr['difference']}")
        out.append("")
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    batch = Path(sys.argv[1]).resolve()
    terms, pairs = load_batch(batch)
    target = batch.with_name(batch.stem + "_미리보기.md")
    target.write_text(render(terms, pairs, batch.stem), encoding="utf-8", newline="\n")
    print(f"미리보기: {target}")


if __name__ == "__main__":
    main()
