"""후보: 이미 있는 용어 11개에 면접 질문·30초 모범 답변 채우기 (2026-11-11)
면접 답은 해 보지 않은 일을 해 본 것처럼 쓰지 않는다 → "이렇게 판단하겠습니다" 형식.

미리보기:  python pipeline/candidates/2026-11-11_모범답변.py --preview   (읽기 쉬운 .md 파일을 만든다)
승인 후:   python pipeline/candidates/2026-11-11_모범답변.py --apply     (glossary.json에 넣고 검사, 실패하면 되돌림)
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "site" / "data" / "glossary.json"

UPDATES = {
    "paas": (
        "PaaS를 쓰자고 할 때 고객에게 꼭 확인할 것은 무엇인가요?",
        "앱이 PaaS의 틀 안에서 돌 수 있는지를 먼저 확인하겠습니다. 특별한 프로그램을 설치해야 하거나, 서버 파일에 직접 저장하거나, 운영체제 설정을 바꿔야 하면 PaaS에서 막힐 수 있습니다. 그런 제약이 없으면 서버 관리를 맡기고 기능 개발에 집중할 수 있어서 작은 팀에 유리하다고 판단합니다.",
    ),
    "saas": (
        "직접 만들지, SaaS를 도입할지 어떻게 판단하나요?",
        "먼저 그 기능이 고객의 차별점인지를 보겠습니다. 메일 발송, 결제, 일정 관리처럼 어느 회사나 비슷하게 쓰는 기능은 SaaS가 빠르고 쌉니다. 고객만의 업무 방식이 핵심이라 딱 맞게 바꿔야 하는 부분만 직접 만드는 것이 좋다고 판단합니다. 도입 전에는 데이터를 밖으로 내보낼 수 있는지도 확인합니다.",
    ),
    "msa": (
        "서비스를 마이크로서비스로 나누면 무엇이 어려워지나요?",
        "서비스끼리 주고받는 통신이 늘어나서, 장애가 났을 때 원인을 찾기 어려워진다고 알고 있습니다. 그래서 나누기 전에 요청 흐름을 따라갈 수 있는 관측성과 자동 배포를 먼저 갖추겠습니다. 그리고 전부를 한 번에 나누기보다, 따로 늘려야 하는 기능 하나부터 떼어 내겠습니다.",
    ),
    "rdb": (
        "새 프로젝트에서 데이터베이스는 무엇으로 시작하겠어요?",
        "특별한 이유가 없으면 RDB로 시작하겠습니다. 주문, 결제, 회원처럼 정확성과 관계가 중요한 데이터가 대부분이고, SQL로 조회하기 쉽고 아는 사람도 많기 때문입니다. 데이터 모양이 자주 바뀌거나 양이 아주 많아지는 부분이 생기면 그 부분만 NoSQL을 검토하겠습니다.",
    ),
    "nosql": (
        "어떤 데이터를 NoSQL에 두는 것이 좋을까요?",
        "모양이 자주 바뀌거나 양이 아주 많고, 표끼리 복잡하게 묶어 조회할 일이 적은 데이터라고 판단합니다. 예를 들어 채팅 기록, 행동 로그, 상품마다 항목이 다른 설명 같은 것입니다. 다만 돈이나 재고처럼 숫자가 정확해야 하는 데이터는 RDB에 두겠습니다.",
    ),
    "vector-db": (
        "벡터 DB만으로 검색하면 어떤 문제가 생길 수 있나요?",
        "뜻이 비슷한 글은 잘 찾지만, 제품 번호나 사람 이름처럼 글자가 정확히 맞아야 하는 검색은 놓치기 쉽다고 알고 있습니다. 그래서 고객 질문에 이런 고유 이름이 많으면, 키워드 검색과 벡터 검색을 함께 쓰는 하이브리드 검색을 검토하겠습니다. 실제 질문 목록으로 두 방식을 비교해서 정하겠습니다.",
    ),
    "chunking": (
        "문서를 어떤 크기로 나눌지 어떻게 정하나요?",
        "정답이 있는 것은 아니라서, 실제 질문으로 비교해서 정하겠습니다. 먼저 제목과 문단 경계에서 자르고, 앞뒤 조각을 조금 겹치게 둡니다. 그다음 크기를 두세 가지로 바꿔 가며, 같은 질문 목록에서 정답 문서가 위쪽에 나오는 비율을 재서 가장 좋은 쪽을 고르겠습니다.",
    ),
    "context-window": (
        "긴 문서를 AI에게 다 넣을 수 없을 때 어떻게 하나요?",
        "필요한 부분만 골라 넣는 방법을 먼저 쓰겠습니다. 질문과 관련된 조각을 검색해서 넣는 RAG가 대표적입니다. 대화가 길어지면 오래된 내용은 요약해서 넣고, 지시문처럼 꼭 필요한 것은 앞쪽에 둡니다. 많이 넣을수록 비용이 늘고 중간 내용을 놓치기 쉬워서, 덜 넣는 쪽이 오히려 낫다고 판단합니다.",
    ),
    "agentic-coding": (
        "AI 에이전트에게 개발을 맡길 때 사람은 무엇을 하나요?",
        "끝났다고 볼 기준을 정하고, 결과를 검토해 승인하는 일을 하겠습니다. 기준은 시험으로 확인할 수 있게 쓰고, AI가 시험만 통과하도록 엉뚱하게 만들지 않았는지도 봅니다. 되돌리기 어려운 작업, 예를 들어 배포나 데이터 삭제는 사람이 직접 승인하게 두겠습니다.",
    ),
    "prompt-injection": (
        "AI가 외부 문서를 읽는 서비스에서 프롬프트 인젝션을 어떻게 막겠어요?",
        "AI가 읽어 온 글은 명령이 아니라 데이터로만 다루게 구역을 나누겠습니다. 그리고 AI가 쓸 수 있는 도구의 권한을 꼭 필요한 만큼으로 줄이고, 메일 보내기나 삭제처럼 되돌리기 어려운 행동은 사람 승인을 거치게 합니다. 지시문에 '무시해'라고 쓰는 것만으로는 막을 수 없어서, 여러 겹으로 막는 것이 맞다고 판단합니다.",
    ),
    "smoke-test": (
        "배포 직후에 무엇을 확인하나요?",
        "가장 중요한 기능 몇 가지만 빠르게 돌려 보는 스모크 테스트를 하겠습니다. 예를 들어 첫 화면이 열리는지, 로그인과 핵심 기능 하나가 되는지입니다. 여기서 실패하면 원인을 찾기 전에 먼저 이전 버전으로 되돌려 사용자 피해를 줄이고, 그다음에 자세히 살펴보겠습니다.",
    ),
}


def load():
    return DATA.read_text(encoding="utf-8")


def apply(text):
    """기존 파일 모양을 그대로 두고, 각 용어의 "examples" 줄 바로 앞에 두 칸을 끼운다."""
    data = json.loads(text)
    by_id = {t["id"]: t for t in data["terms"]}
    for tid, (q, a) in UPDATES.items():
        term = by_id.get(tid)
        if term is None:
            sys.exit(f"없는 용어: {tid}")
        if "interview_q" in term or "interview_a" in term:
            sys.exit(f"이미 면접 칸이 있음: {tid} (덮어쓰지 않음)")
        start = text.index(f'"id": "{tid}"')
        ex_at = text.index('      "examples": [', start)
        insert = (f'      "interview_q": {json.dumps(q, ensure_ascii=False)},\n'
                  f'      "interview_a": {json.dumps(a, ensure_ascii=False)},\n')
        text = text[:ex_at] + insert + text[ex_at:]
        up_at = text.index('"updated_at": "', start)
        end = text.index('"', up_at + len('"updated_at": "'))
        text = text[:up_at] + f'"updated_at": "{date.today().isoformat()}' + text[end:]
    json.loads(text)
    return text


def preview():
    data = json.loads(load())
    by_id = {t["id"]: t for t in data["terms"]}
    lines = ["# 모범 답변 미리보기 (승인 전)", "", f"- 대상: {len(UPDATES)}개 용어", "- 형식: 해 보지 않은 일은 \"이렇게 판단하겠습니다\"로 씀", ""]
    for n, (tid, (q, a)) in enumerate(UPDATES.items(), 1):
        t = by_id[tid]
        lines += [f"## {n}. {t['term_en']} · {t['term_ko']}", "", f"**뜻**: {t['definition']}", "",
                  f"**면접 질문**: {q}", "", f"**30초 모범 답변**", "", f"> {a}", "", f"(약 {len(a)}자)", ""]
    out = Path(__file__).with_name("2026-11-11_모범답변_미리보기.md")
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"미리보기: {out}")


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview()
    elif "--apply" in sys.argv:
        original = load()
        DATA.write_text(apply(original), encoding="utf-8", newline="\n")
        sys.path.insert(0, str(ROOT / "pipeline"))
        import validate  # noqa: E402
        schema = json.loads(validate.SCHEMA_PATH.read_text(encoding="utf-8"))
        data = json.loads(load())
        errors = validate.check_schema(data, schema)
        if errors:
            DATA.write_text(original, encoding="utf-8", newline="\n")
            sys.exit("검사 실패, 원래대로 되돌렸습니다:\n" + "\n".join(map(str, errors)))
        print(f"✅ {len(UPDATES)}개 용어에 면접 질문·모범 답변을 넣었습니다. 앱에서 확인한 뒤 커밋하세요.")
    else:
        print(__doc__)
