"""후보: 122개 용어에 발음 기호(IPA: International Phonetic Alphabet, 국제 음성 기호) 넣기 (2026-11-12)
- 미국 영어 기준. 화면에는 /…/ 로 감싸 보여 준다.
- 한글 현업 발음(pronunciation.ko)은 지우지 않는다. 한국 현업에서 읽는 방식(PoC=피오씨)은 발음 기호로 나타낼 수 없기 때문.
- 약어(letters)는 글자를 하나씩 읽는 소리를 적는다.

미리보기:  python pipeline/candidates/2026-11-12_발음기호.py --preview
승인 후:   python pipeline/candidates/2026-11-12_발음기호.py --apply   (실패하면 되돌림)
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "site" / "data" / "glossary.json"

IPA = {
    "polling": "ˈpoʊlɪŋ", "webhook": "ˈwɛbhʊk", "oauth": "ˈoʊɔθ", "design-token": "dɪˈzaɪn ˌtoʊkən",
    "requirements": "rɪˈkwaɪərmənts", "stakeholder": "ˈsteɪkˌhoʊldər", "user-interview": "ˈjuzər ˈɪntərˌvju",
    "hypothesis-validation": "haɪˈpɑθəsɪs ˌvæləˈdeɪʃən", "mvp": "ˌɛmviˈpi", "poc": "ˌpioʊˈsi",
    "moscow": "ˈmɑskoʊ", "scope-creep": "ˈskoʊp ˌkrip", "pivot": "ˈpɪvət", "baseline": "ˈbeɪsˌlaɪn",
    "api": "ˌeɪpiˈaɪ", "json": "ˈdʒeɪsən", "schema": "ˈskimə", "data-modeling": "ˈdeɪtə ˌmɑdəlɪŋ",
    "architecture": "ˈɑrkɪˌtɛktʃər", "adr": "ˌeɪdiˈɑr", "separation-of-concerns": "ˌsɛpəˈreɪʃən əv kənˈsɝnz",
    "adapter-pattern": "əˈdæptər ˌpætərn", "static-site": "ˈstætɪk ˈsaɪt", "single-source-of-truth": "ˈsɪŋɡəl ˈsɔrs əv ˈtruθ",
    "git": "ɡɪt", "branch": "bræntʃ", "commit": "kəˈmɪt", "pull-request": "ˈpʊl rɪˌkwɛst", "code-review": "ˈkoʊd rɪˌvju",
    "frontend": "ˈfrʌntˌɛnd", "backend": "ˈbækˌɛnd", "library": "ˈlaɪˌbrɛri", "framework": "ˈfreɪmˌwɝk",
    "environment-variable": "ɪnˈvaɪrənmənt ˈvɛriəbəl", "refactoring": "riˈfæktərɪŋ", "unit-test": "ˈjunɪt ˌtɛst",
    "integration-test": "ˌɪntəˈɡreɪʃən ˌtɛst", "validation": "ˌvæləˈdeɪʃən", "regression": "rɪˈɡrɛʃən",
    "edge-case": "ˈɛdʒ ˌkeɪs", "mock-api": "ˈmɑk ˌeɪpiˈaɪ", "evaluation-dataset": "ɪˌvæljuˈeɪʃən ˈdeɪtəˌsɛt",
    "dogfooding": "ˈdɔɡˌfudɪŋ", "qa": "ˌkjuˈeɪ", "ci-cd": "ˌsiˈaɪ ˌsiˈdi", "pipeline": "ˈpaɪpˌlaɪn",
    "deployment": "dɪˈplɔɪmənt", "staging": "ˈsteɪdʒɪŋ", "production": "prəˈdʌkʃən", "rollback": "ˈroʊlˌbæk",
    "cache": "kæʃ", "pwa": "ˌpi ˌdʌbəljuˈeɪ", "serverless": "ˈsɝvərləs", "log": "lɔɡ", "monitoring": "ˈmɑnɪtərɪŋ",
    "incident": "ˈɪnsɪdənt", "sla": "ˌɛsɛlˈeɪ", "availability": "əˌveɪləˈbɪləti",
    "root-cause-analysis": "ˈrut ˈkɔz əˈnæləsɪs", "hotfix": "ˈhɑtˌfɪks", "rate-limit": "ˈreɪt ˌlɪmɪt",
    "token": "ˈtoʊkən", "authentication": "ɔˌθɛntɪˈkeɪʃən", "authorization": "ˌɔθərəˈzeɪʃən", "sso": "ˌɛsɛsˈoʊ",
    "passkey": "ˈpæsˌki", "mfa": "ˌɛmɛfˈeɪ", "threat-modeling": "ˈθrɛt ˌmɑdəlɪŋ", "least-privilege": "ˈlist ˈprɪvəlɪdʒ",
    "defense-in-depth": "dɪˈfɛns ɪn ˈdɛpθ", "data-minimization": "ˈdeɪtə ˌmɪnəməˈzeɪʃən",
    "de-identification": "ˌdiaɪˌdɛntəfəˈkeɪʃən", "multi-tenancy": "ˌmʌltiˈtɛnənsi", "i18n": "ˌaɪ eɪˈtin ˈɛn",
    "l10n": "ˌɛl ˈtɛn ˈɛn", "ab-test": "ˌeɪˈbi ˌtɛst", "scalability": "ˌskeɪləˈbɪləti", "technical-debt": "ˈtɛknɪkəl ˈdɛt",
    "feature-flag": "ˈfitʃər ˌflæɡ", "onboarding": "ˈɑnˌbɔrdɪŋ", "churn": "tʃɝn", "llm": "ˌɛlɛlˈɛm", "prompt": "prɑmpt",
    "rag": "ræɡ", "hallucination": "həˌlusəˈneɪʃən", "ai-agent": "ˌeɪˈaɪ ˌeɪdʒənt", "orchestration": "ˌɔrkəˈstreɪʃən",
    "llmops": "ˌɛlɛlˈɛm ˌɑps", "feedback-loop": "ˈfidˌbæk ˌlup", "llm-as-a-judge": "ˌɛlɛlˈɛm æz ə ˈdʒʌdʒ",
    "human-in-the-loop": "ˈhjumən ɪn ðə ˈlup", "contract": "ˈkɑnˌtrækt", "trade-off": "ˈtreɪdˌɔf",
    "leitner-system": "ˈlaɪtnər ˌsɪstəm", "peak-end-rule": "ˈpik ˈɛnd ˌrul", "hypercorrection-effect": "ˌhaɪpərkəˈrɛkʃən ɪˌfɛkt",
    "hash-routing": "ˈhæʃ ˌraʊtɪŋ", "dry-run": "ˈdraɪ ˌrʌn", "cache-busting": "ˈkæʃ ˌbʌstɪŋ", "xss": "ˌɛksɛsˈɛs",
    "supply-chain-attack": "səˈplaɪ ˌtʃeɪn əˈtæk", "iaas": "ˈaɪæs", "paas": "pæs", "saas": "sæs",
    "on-premise": "ˌɑnˈprɛmɪs", "container": "kənˈteɪnər", "monolith": "ˈmɑnəlɪθ", "msa": "ˌɛmɛsˈeɪ", "rdb": "ˌɑrdiˈbi",
    "nosql": "ˌnoʊˌɛskjuˈɛl", "embedding": "ɛmˈbɛdɪŋ", "vector-db": "ˈvɛktər ˈdeɪtəˌbeɪs", "chunking": "ˈtʃʌŋkɪŋ",
    "context-window": "ˈkɑntɛkst ˌwɪndoʊ", "mcp": "ˌɛmsiˈpi", "vibe-coding": "ˈvaɪb ˌkoʊdɪŋ",
    "agentic-coding": "eɪˈdʒɛntɪk ˌkoʊdɪŋ", "guardrail": "ˈɡɑrdˌreɪl", "prompt-injection": "ˈprɑmpt ɪnˌdʒɛkʃən",
    "acceptance-criteria": "əkˈsɛptəns kraɪˈtɪriə", "smoke-test": "ˈsmoʊk ˌtɛst", "observability": "əbˌzɝvəˈbɪləti",
}

# 영어 발음과 한국 현업 발음이 눈에 띄게 다른 것 (미리보기에 표시)
NOTES = {
    "routing": "라우팅: 미국 개발자는 대부분 '라우팅'(ˈraʊtɪŋ), 영국은 '루팅'(ˈrutɪŋ)",
    "moscow": "도시 Moscow와 같은 소리. 한국 회의에서는 '모스크바'라고도 함",
    "oauth": "O를 한 글자로 읽고 auth를 붙임",
    "churn": "한국 현업은 '천'보다 '이탈'이라고 더 많이 말함",
    "json": "'제이슨'. 사람 이름 Jason과 같은 소리",
    "iaas": "'아이아스'. '이아스'라고도 함",
}


def load():
    return DATA.read_text(encoding="utf-8")


def apply(text):
    data = json.loads(text)
    ids = [t["id"] for t in data["terms"]]
    missing = [i for i in ids if i not in IPA]
    extra = [i for i in IPA if i not in ids]
    if missing or extra:
        sys.exit(f"목록이 맞지 않음. 빠짐: {missing} / 없는 용어: {extra}")
    for tid in ids:
        start = text.index(f'"id": "{tid}"')
        p_at = text.index('"pronunciation": {', start)
        ra = re.compile(r'"read_as": "(letters|word|mixed)"').search(text, p_at)
        if '"ipa"' in text[p_at:text.index("}", p_at)]:
            sys.exit(f"이미 ipa가 있음: {tid}")
        insert = f', "ipa": {json.dumps(IPA[tid], ensure_ascii=False)}'
        text = text[:ra.end()] + insert + text[ra.end():]
        up_at = text.index('"updated_at": "', start)
        end = text.index('"', up_at + len('"updated_at": "'))
        text = text[:up_at] + f'"updated_at": "{date.today().isoformat()}' + text[end:]
    json.loads(text)
    return text


def preview():
    data = json.loads(load())
    stage_name = {"discovery": "① 발견·기획", "design": "② 설계", "build": "③ 개발", "test": "④ 테스트·품질",
                  "deploy": "⑤ 배포", "operate": "⑥ 운영", "secure": "⑦ 보안·개인정보", "grow": "⑧ 개선·확장",
                  "automate": "⑨ 자동화·지속 개선"}
    lines = ["# 발음 기호 미리보기 (승인 전)", "",
             "- 기준: 미국 영어 IPA. 화면에는 `/…/`로 표시하고, 한글 현업 발음은 그대로 함께 보여 줍니다.",
             "- 읽는 법: ˈ 다음 음절을 가장 세게, ˌ 다음 음절을 조금 세게 읽습니다. ɝ·ər은 혀를 말아 내는 '얼' 소리입니다.",
             "- 고칠 것이 있으면 '용어 이름 → 고칠 발음'으로 알려 주세요.", ""]
    for stage, label in stage_name.items():
        rows = [t for t in data["terms"] if t["stage"] == stage]
        lines += [f"## {label} ({len(rows)}개)", "", "| 용어 | 발음 기호 | 현업 발음 | 참고 |", "|---|---|---|---|"]
        for t in rows:
            note = NOTES.get(t["id"], "")
            if t["id"] == "hash-routing":
                note = NOTES["routing"]
            kind = {"letters": "약어(한 글자씩)", "mixed": "섞어 읽기"}.get(t["pronunciation"]["read_as"], "")
            note = " · ".join(x for x in [kind, note] if x)
            lines.append(f"| **{t['term_en']}** | /{IPA[t['id']]}/ | {t['pronunciation']['ko']} | {note} |")
        lines.append("")
    out = Path(__file__).with_name("2026-11-12_발음기호_미리보기.md")
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"미리보기: {out} ({len(IPA)}개)")


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview()
    elif "--apply" in sys.argv:
        original = load()
        DATA.write_text(apply(original), encoding="utf-8", newline="\n")
        sys.path.insert(0, str(ROOT / "pipeline"))
        import validate  # noqa: E402
        schema = json.loads(validate.SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = validate.check_schema(json.loads(load()), schema)
        if errors:
            DATA.write_text(original, encoding="utf-8", newline="\n")
            sys.exit("검사 실패, 원래대로 되돌렸습니다:\n" + "\n".join(map(str, errors)))
        print(f"✅ {len(IPA)}개 용어에 발음 기호를 넣었습니다.")
    else:
        print(__doc__)
