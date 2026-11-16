"""후보: 2026-11-17에 넣은 용어 중 면접 질문·30초 모범 답변이 빠진 15개 채우기 (2026-11-17)
면접 답은 해 보지 않은 일을 해 본 것처럼 쓰지 않는다 → "이렇게 판단하겠습니다" 형식.

미리보기:  python pipeline/candidates/2026-11-17_모범답변.py --preview
승인 후:   python pipeline/candidates/2026-11-17_모범답변.py --apply   (실패하면 되돌림)
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "site" / "data" / "glossary.json"

UPDATES = {
    "virtual-machine": (
        "가상 머신과 컨테이너 중 무엇을 쓸지 어떻게 판단하나요?",
        "운영체제까지 직접 손대야 하는지를 먼저 보겠습니다. 고객사 보안 프로그램을 운영체제에 깔아야 하거나 특정 운영체제 설정이 필요하면 가상 머신이 맞습니다. 앱만 가볍게 여러 개 띄우고 빨리 배포하고 싶다면 컨테이너가 낫다고 판단합니다. 둘 중 하나만 고르지 않고, 가상 머신 위에 컨테이너를 올리는 경우도 많습니다.",
    ),
    "autoscaling": (
        "오토스케일링을 켤 때 꼭 정해야 할 것은 무엇인가요?",
        "최소 대수와 최대 대수, 그리고 언제 늘릴지 기준을 정하겠습니다. 최대 대수가 없으면 공격이나 버그로 요청이 폭증할 때 요금이 끝없이 늘 수 있습니다. 또 서버가 켜지는 데 몇 분 걸리니, 행사처럼 미리 아는 날은 자동 확장만 믿지 않고 서버를 먼저 늘려 두는 것이 안전하다고 판단합니다.",
    ),
    "dns": (
        "서버를 옮긴 뒤 일부 사용자만 접속이 안 된다면 무엇을 의심하나요?",
        "DNS가 아직 다 퍼지지 않았을 가능성을 먼저 보겠습니다. 사용자 쪽에 옛 주소가 기억돼 있으면 옛 서버로 가기 때문입니다. 그래서 옮기기 전에 기억 시간(TTL)을 짧게 줄이고, 옮긴 뒤에도 한동안 옛 서버를 켜 두는 순서로 계획하겠습니다.",
    ),
    "cdn": (
        "해외 사용자가 화면이 느리다고 하면 무엇부터 해 보겠어요?",
        "느린 것이 화면 파일인지, 서버 응답인지부터 나눠 보겠습니다. 이미지나 화면 파일이 느리다면 CDN으로 사용자와 가까운 곳에서 보내게 하는 것이 가장 효과가 큽니다. 이때 배포할 때마다 파일 이름이나 버전을 바꿔서, CDN이 옛 파일을 계속 보내지 않게 하겠습니다.",
    ),
    "availability-zone": (
        "클라우드에서 서비스가 멈추지 않게 하려면 서버를 어디에 두겠어요?",
        "같은 지역 안의 가용 영역 두 곳 이상에 나눠 두겠습니다. 한 영역이 정전이나 장애로 멈춰도 다른 영역이 서비스를 이어 갑니다. 이때 서버만이 아니라 데이터베이스와 저장소도 함께 나눠야 하고, 지역 전체가 멈추는 경우까지 대비할지는 고객의 목표와 비용을 보고 정하겠습니다.",
    ),
    "spof": (
        "시스템에서 단일 장애점을 어떻게 찾겠어요?",
        "요청이 들어와서 답이 나갈 때까지 거치는 것을 모두 적고, 하나씩 '이것만 멈추면 전체가 멈추는가'를 물어보겠습니다. 서버나 데이터베이스뿐 아니라 외부 API, 인증 서비스, 한 사람만 아는 배포 방법도 단일 장애점이 될 수 있습니다. 찾은 것은 영향이 큰 순서로 이중화하거나 문서로 남기겠습니다.",
    ),
    "failover": (
        "이중화를 해 두었는데도 장애 때 서비스가 멈췄다면 무엇을 의심하나요?",
        "여분으로 실제로 넘어가는지 시험한 적이 없었을 가능성을 먼저 보겠습니다. 앱이 옛 서버 주소를 계속 쓰거나, 여분 쪽 데이터가 뒤처져 있으면 넘어가도 제대로 동작하지 않습니다. 그래서 정기적으로 일부러 페일오버를 해 보고, 몇 초 만에 넘어가는지와 데이터가 맞는지를 기록하겠습니다.",
    ),
    "disaster-recovery": (
        "고객이 재해 복구 계획을 요구하면 무엇부터 정하겠어요?",
        "얼마나 빨리 다시 살려야 하는지(RTO)와 어느 시점 데이터까지 되살려야 하는지(RPO)를 고객과 숫자로 먼저 정하겠습니다. 그 숫자에 맞춰 백업만 할지, 다른 지역에 대기 환경을 둘지 정하고 비용을 함께 보여 드립니다. 계획서만 두지 않고, 1년에 한 번은 실제로 옮겨 보는 훈련을 넣겠습니다.",
    ),
    "rto": (
        "RTO를 1시간으로 약속하면 무엇을 준비해야 하나요?",
        "1시간 안에 다시 살릴 수 있는 절차와 장비가 있어야 합니다. 서버를 처음부터 새로 만들면 1시간을 넘기기 쉬우니, 대기 서버나 코드형 인프라로 바로 만들 수 있게 준비하겠습니다. 그리고 복구 훈련으로 실제 걸리는 시간을 재서, 약속한 시간 안에 드는지 확인하겠습니다.",
    ),
    "rpo": (
        "RPO와 백업 주기는 어떤 관계인가요?",
        "백업 주기가 곧 잃을 수 있는 데이터의 양입니다. 하루에 한 번 백업하면 최대 하루 치를 잃을 수 있어서 RPO는 하루가 됩니다. 고객이 RPO 5분을 원하면 백업만으로는 부족하고, 데이터를 실시간으로 복제하는 방식을 써야 한다고 판단합니다.",
    ),
    "latency": (
        "사용자가 느리다고 할 때 무엇부터 재겠어요?",
        "평균 응답 시간만 보지 않고, 느린 쪽 상위 1%(p99) 시간을 함께 재겠습니다. 평균이 괜찮아도 일부 사용자는 아주 느릴 수 있기 때문입니다. 그다음 요청이 지나가는 단계별 시간을 나눠서, 네트워크인지 데이터베이스인지 AI 모델 호출인지 어디서 오래 걸리는지 찾겠습니다.",
    ),
    "throughput": (
        "처리량을 올리면 응답 속도도 좋아지나요?",
        "꼭 그렇지는 않습니다. 요청을 모아서 한꺼번에 처리하면 처리량은 늘지만, 각 요청은 모일 때까지 기다리느라 오히려 느려질 수 있습니다. 그래서 고객에게 중요한 것이 많이 처리하는 것인지, 한 건씩 빨리 답하는 것인지 먼저 정하고 둘을 함께 재면서 조정하겠습니다.",
    ),
    "uptime": (
        "가동률 99.9%와 99.99%의 차이를 고객에게 어떻게 설명하겠어요?",
        "멈출 수 있는 시간으로 바꿔서 설명하겠습니다. 99.9%는 한 달에 약 43분, 99.99%는 약 4분까지 멈출 수 있다는 뜻입니다. 9를 하나 더 붙이려면 이중화와 자동 전환, 운영 인력까지 비용이 몇 배로 늘기 때문에, 업무에 꼭 필요한 수준을 함께 정하자고 제안하겠습니다.",
    ),
    "firewall": (
        "데이터베이스를 외부 공격으로부터 어떻게 지키겠어요?",
        "먼저 데이터베이스는 인터넷에서 바로 들어올 수 없게 방화벽으로 막고, 앱 서버에서만 접속되게 하겠습니다. 열어야 하는 문은 꼭 필요한 주소와 포트만 열고, 왜 열었는지 기록합니다. 방화벽 하나에만 기대지 않고 접속 계정의 권한도 최소로 줄여 여러 겹으로 지키겠습니다.",
    ),
    "critic-agent": (
        "AI 답변에 근거 없는 내용이 섞이는 것을 어떻게 줄이겠어요?",
        "답을 내보내기 전에 검사하는 단계를 두겠습니다. 비평가 역할의 AI가 초안의 주장마다 참고 문서와 맞는지 확인하고, 어긋나면 다시 쓰게 돌려보냅니다. 다시 쓰기는 두세 번으로 제한하고, 그래도 근거가 없으면 모른다고 답하거나 사람에게 넘기게 하겠습니다.",
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
    out = Path(__file__).with_name("2026-11-17_모범답변_미리보기.md")
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
