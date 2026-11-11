"""후보 묶음: 면접 예상 질문 문서와 필드워드 개발 과정에서 나온 용어 (2026-11-11)
검사:  python pipeline/promote.py pipeline/candidates/2026-11-11_면접문서.py --dry-run
승인:  python pipeline/promote.py pipeline/candidates/2026-11-11_면접문서.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from seedlib import add, ex, src  # noqa: E402

P = lambda label: src("planning", f"기획 2026-11-11 ({label})", "2026-11-11")

TERMS = [
    # ---------------- ② 설계 ----------------
    dict(id="contract", term_en="Contract", term_ko="계약 (데이터·API 약속)", aliases=["API 계약", "데이터 계약", "인터페이스 약속", "컨트랙트"],
         pronunciation={"ko": "컨트랙트", "read_as": "word", "note": "회의에서는 '계약' 또는 'API 스펙'이라고도 말합니다"},
         stage="design", level=3,
         definition="두 시스템이 주고받는 데이터의 모양을 미리 정해 둔 약속입니다. 약속만 지키면 한쪽이 안을 바꿔도 다른 쪽은 깨지지 않습니다.",
         analogy="택배 상자 규격. 규격만 맞으면 보내는 사람이 안에 무엇을 넣든, 받는 쪽 선반에 그대로 들어갑니다.",
         pitfall="약속을 글로만 적어 두고 자동으로 검사하지 않으면, 누군가 몰래 칸 이름을 바꿔도 운영 중에야 알게 됩니다. 스키마로 적고 배포 전에 검사합니다.",
         interview_q="두 팀(또는 두 시스템)이 따로 개발할 때 서로 깨지지 않게 하려면 어떻게 하나요?",
         interview_a="주고받는 데이터의 모양을 계약으로 먼저 정합니다. 학습 앱에서는 관리 도구와 공개 사이트가 용어 데이터 파일 하나로만 이어지게 하고, 그 파일의 모양을 JSON 스키마로 적어 배포할 때마다 자동으로 검사했습니다. 그래서 한쪽을 고쳐도 계약만 지키면 다른 쪽은 그대로 동작합니다.",
         examples=ex(("meeting", "프런트와 백엔드가 동시에 개발하려면, 응답 형식 계약부터 오늘 확정하시죠."),
                     ("interview", "관리 도구와 사이트를 데이터 파일 하나의 계약으로만 이어서, 서로 따로 고칠 수 있게 했습니다."),
                     ("review", "응답에 칸 이름이 바뀌었어요. 계약이 깨지니 스키마부터 함께 고쳐 주세요.")),
         tags=["설계", "데이터"], related=["schema", "api", "separation-of-concerns"], sources=P("면접 문서: 관리 도구와 사이트를 잇는 파일")),

    dict(id="trade-off", term_en="Trade-off", term_ko="트레이드오프 (맞바꾸기)", aliases=["트레이드 오프", "득실", "맞교환", "대가"],
         pronunciation={"ko": "트레이드오프", "read_as": "word"},
         stage="design", also_stages=["discovery"], level=2,
         definition="하나를 얻으려면 다른 하나를 내줘야 하는 관계입니다. 좋은 설계는 무엇을 얻고 무엇을 포기했는지 알고 고르는 것입니다.",
         analogy="빠른 택배는 비싸고, 싼 택배는 느립니다. 둘 다 가질 수는 없어서 상황에 맞게 고릅니다.",
         pitfall="장점만 말하고 대가를 숨기면, 나중에 그 대가가 문제로 터졌을 때 신뢰를 잃습니다. 결정할 때 포기한 것도 같이 적어 둡니다.",
         interview_q="프로젝트에서 내린 결정의 트레이드오프를 하나 설명해 주세요.",
         interview_a="학습 앱을 서버 없는 정적 사이트로 만들었습니다. 무료로 올릴 수 있고 공격받을 서버가 없다는 것을 얻었지만, 사용자 데이터를 모아 분석할 수 없다는 대가가 있었습니다. 그 대가는 공개할 때 사용자에게 먼저 알리고, 의견 보내기로 보완했습니다.",
         examples=ex(("meeting", "캐시를 길게 잡으면 빨라지지만 새 데이터가 늦게 보입니다. 이 트레이드오프를 고객과 먼저 정하시죠."),
                     ("interview", "정적 사이트를 고른 트레이드오프는 비용과 보안을 얻고 데이터 수집을 포기한 것입니다."),
                     ("review", "이 방식이 더 빠른 건 맞는데, 메모리를 두 배 씁니다. 트레이드오프를 설명에 적어 주세요.")),
         tags=["설계", "의사결정"], related=["adr", "architecture", "technical-debt"], sources=P("면접 문서: 트레이드오프를 같이 말하기")),

    dict(id="leitner-system", term_en="Leitner System", term_ko="라이트너 상자 (간격 반복 복습)", aliases=["라이트너 시스템", "간격 반복", "Spaced Repetition", "SRS"],
         pronunciation={"ko": "라이트너 시스템", "read_as": "word", "note": "독일 사람 이름 Leitner에서 왔습니다"},
         stage="design", level=3,
         definition="카드를 여러 상자에 나눠, 맞히면 복습 간격이 긴 다음 상자로, 틀리면 앞 상자로 옮기는 복습 방법입니다. 잘 아는 것은 드물게, 약한 것은 자주 보게 됩니다.",
         analogy="성적에 따라 반을 옮기는 학원. 잘하면 한 달에 한 번 시험, 못하면 매일 보충 수업.",
         pitfall="오래 기억하던 카드를 한 번 틀렸다고 맨 처음 상자로 돌리면 사용자가 지쳐 그만둡니다. 높은 상자는 몇 칸만 내리는 식으로 조정합니다.",
         interview_q="학습 앱의 복습 날짜는 어떻게 정했나요?",
         interview_a="라이트너 상자 7개를 써서 1·2·4·7·15·30·60일 간격으로 다시 묻게 했습니다. 맞히면 다음 상자로, 틀리면 앞으로 옮기되, 상자 4 이상에서 틀리면 두 칸만 내립니다. 이 규칙은 화면과 분리해서 단위 테스트로 검증했습니다.",
         examples=ex(("meeting", "복습 알고리즘은 처음엔 단순한 라이트너 상자로 시작하고, 데이터가 쌓이면 바꾸시죠."),
                     ("interview", "라이트너 상자 규칙을 화면 코드와 떼어 내서, 날짜를 바꿔 가며 시험할 수 있게 했습니다.")),
         tags=["학습 과학", "설계"], related=["unit-test", "separation-of-concerns"], sources=P("필드워드 복습 규칙")),

    dict(id="peak-end-rule", term_en="Peak-End Rule", term_ko="피크엔드 법칙", aliases=["피크 엔드 법칙", "절정과 끝 효과"],
         pronunciation={"ko": "피크엔드 법칙", "read_as": "word"},
         stage="design", also_stages=["grow"], level=3,
         definition="사람은 경험 전체를 고르게 기억하지 않고, 가장 강렬했던 순간과 마지막 순간으로 전체를 판단한다는 심리 법칙입니다. 서비스의 끝 화면을 공들여 만드는 이유입니다.",
         analogy="여행 중 고생이 많았어도, 마지막 날 노을이 멋지면 '좋은 여행'으로 기억하는 것.",
         pitfall="마지막 화면을 '틀린 문제 목록'처럼 아쉬운 것으로 끝내면, 내용이 좋았어도 다음에 다시 오고 싶지 않게 됩니다.",
         interview_q="사용자 경험에서 끝 화면이 왜 중요한가요?",
         interview_a="피크엔드 법칙 때문에 사람은 마지막 순간으로 전체를 기억합니다. 학습 앱에서는 마무리 문제의 마지막을 꼭 맞힐 수 있는 카드로 두고, 끝 화면에서 '오늘 바로잡은 용어'를 이름까지 들어 칭찬하게 했습니다.",
         examples=ex(("meeting", "결제 완료 화면이 너무 밋밋해요. 피크엔드 법칙을 생각하면 여기서 감사 인사를 확실히 하시죠."),
                     ("review", "마지막 단계에 오류 안내만 남아 있어요. 피크엔드 법칙상 성공 메시지로 끝내 주세요.")),
         tags=["학습 과학", "사용자 경험"], related=["onboarding", "churn"], sources=P("오늘의 마무리 설계")),

    dict(id="hypercorrection-effect", term_en="Hypercorrection Effect", term_ko="과잉 교정 효과", aliases=["하이퍼코렉션", "확신 오답 교정 효과"],
         pronunciation={"ko": "하이퍼코렉션 이펙트", "read_as": "word", "note": "우리말로 '과잉 교정 효과'라고 더 자주 말합니다"},
         stage="design", level=4,
         definition="확신했는데 틀린 답을 바로잡으면, 자신 없이 틀린 답보다 오히려 더 잘 기억된다는 학습 현상입니다. 놀람이 기억을 강하게 만들기 때문입니다.",
         analogy="당연히 맞다고 우겼다가 틀린 퀴즈 답은 오래도록 잊히지 않는 것.",
         pitfall="확신하고 틀린 사람을 혼내면 부끄러움 때문에 다음부터 답을 피합니다. '의외죠?'처럼 놀람을 살리고, 바로 정답을 보여 줘야 효과가 납니다.",
         interview_q="학습 앱에서 확신도를 따로 묻는 이유는 무엇인가요?",
         interview_a="맞았는지만 보면 '확신했는데 틀린 착각'을 놓칩니다. 착각은 면접에서 자신 있게 틀린 말을 하게 만드는 가장 위험한 상태입니다. 다행히 과잉 교정 효과 때문에 착각을 바로잡으면 더 잘 기억되므로, 착각을 따로 찾아 보여 주고 바로잡으면 크게 칭찬합니다.",
         examples=ex(("meeting", "확신도를 같이 받으면 착각을 따로 찾을 수 있고, 과잉 교정 효과로 더 오래 기억됩니다."),
                     ("interview", "과잉 교정 효과를 살리려고, 확신하고 틀렸을 때는 빨간 X 대신 내 답과 정답을 나란히 보여 줬습니다.")),
         tags=["학습 과학"], related=["peak-end-rule", "leitner-system"], sources=P("확신도 5단계 설계")),

    # ---------------- ③ 개발 ----------------
    dict(id="hash-routing", term_en="Hash Routing", term_ko="해시 라우팅", aliases=["해시 라우터", "# 주소 방식"],
         pronunciation={"ko": "해시 라우팅", "read_as": "word"},
         stage="build", level=3,
         definition="주소 끝의 # 뒤 부분(예: #/term/api)을 보고 화면을 바꾸는 방식입니다. # 뒤는 서버로 보내지지 않아서, 서버 설정 없이 정적 사이트에서도 여러 화면을 만들 수 있습니다.",
         analogy="한 권의 책 안에서 책갈피 번호만 바꿔 다른 쪽을 펴는 것. 서점(서버)에 다시 갈 필요가 없습니다.",
         pitfall="주소가 # 때문에 덜 깔끔하고, 검색 엔진이 # 뒤 화면을 따로 잘 모으지 않습니다. 검색 노출이 중요하면 다른 방식을 검토합니다.",
         interview_q="서버 없는 정적 사이트에서 여러 화면을 어떻게 만들었나요?",
         interview_a="해시 라우팅을 썼습니다. 주소의 # 뒤 부분이 바뀌면 브라우저가 알려 주고, 그 값에 맞는 화면을 그립니다. # 뒤는 서버로 가지 않아서 GitHub Pages 같은 정적 호스팅에서도 새로고침해도 화면이 깨지지 않습니다.",
         examples=ex(("meeting", "GitHub Pages라서 서버 설정을 못 바꾸니, 해시 라우팅으로 가시죠."),
                     ("review", "카드 화면 주소를 해시 라우팅 규칙에 맞게 #/term/아이디 형식으로 맞춰 주세요.")),
         tags=["화면", "개발"], related=["static-site", "frontend"], sources=P("면접 문서: 프레임워크 없이 만든 것")),

    # ---------------- ④ 테스트·품질 ----------------
    dict(id="dry-run", term_en="Dry Run", term_ko="드라이 런 (시험 실행)", aliases=["드라이런", "시험 실행", "모의 실행"],
         pronunciation={"ko": "드라이 런", "read_as": "word"},
         stage="test", also_stages=["deploy", "automate"], level=2,
         definition="실제로 바꾸지 않고, 바꾸면 어떻게 되는지만 미리 돌려 보는 실행입니다. 되돌리기 어려운 작업 전에 결과를 확인하려고 씁니다.",
         analogy="이삿날 전에 가구 배치를 종이 위에 먼저 그려 보는 것.",
         pitfall="드라이 런 환경이 실제와 다르면 '시험에서는 됐는데 실제로는 실패'가 생깁니다. 실제 데이터의 복사본으로 돌립니다.",
         interview_q="자동화가 공개 데이터를 망가뜨리지 않게 어떻게 막았나요?",
         interview_a="새 용어를 넣는 도구에 드라이 런을 만들었습니다. 원본이 아니라 임시 복사본에 넣어 검사만 하고, 통과하면 사람이 승인한 뒤에 실제로 넣습니다. 실제로 넣다가 오류가 나면 원래대로 되돌립니다.",
         examples=ex(("meeting", "고객 데이터 일괄 수정은 드라이 런으로 바뀔 건수부터 확인하고 진행하겠습니다."),
                     ("review", "삭제 스크립트에 --dry-run 옵션을 추가해 주세요. 지우기 전에 목록을 보고 싶습니다.")),
         tags=["품질", "자동화"], related=["validation", "staging", "human-in-the-loop"], sources=P("promote.py 설계")),

    # ---------------- ⑤ 배포 ----------------
    dict(id="cache-busting", term_en="Cache Busting", term_ko="캐시 버스팅", aliases=["캐시 무효화", "버전 쿼리", "?v="],
         pronunciation={"ko": "캐시 버스팅", "read_as": "word"},
         stage="deploy", also_stages=["build"], level=3,
         definition="파일을 고쳤을 때 브라우저가 저장해 둔 옛 파일을 쓰지 않도록, 파일 주소에 버전 표시를 붙여 새 파일로 받게 하는 방법입니다.",
         analogy="새 메뉴판을 걸면서 '2호'라고 크게 붙여, 손님이 옛 메뉴판을 보지 않게 하는 것.",
         pitfall="코드는 고쳤는데 버전 표시를 안 올리면, 사용자는 한동안 옛 화면을 보고 '안 고쳐졌다'고 신고합니다. 잊지 않도록 자동 검사에 넣습니다.",
         interview_q="배포했는데 사용자에게 옛 화면이 보인다면 무엇을 의심하나요?",
         interview_a="먼저 캐시를 의심합니다. 학습 앱에서도 코드를 고쳤는데 옛 화면이 보인 적이 있어서, 파일 주소 끝에 버전 번호를 붙이고 고칠 때마다 올렸습니다. 사람이 잊을 수 있어서, 파일을 고치고 번호를 안 올리면 자동 점검이 알려 주게 했습니다.",
         examples=ex(("meeting", "배포 후 옛 화면 신고가 많으면 캐시 버스팅이 빠졌는지부터 보겠습니다."),
                     ("review", "app.js를 고쳤는데 ?v= 값이 그대로예요. 캐시 버스팅을 위해 올려 주세요.")),
         tags=["배포", "화면"], related=["cache", "deployment"], sources=P("면접 문서: 캐시 문제")),

    # ---------------- ⑦ 보안·개인정보 ----------------
    dict(id="xss", term_en="XSS", term_ko="크로스 사이트 스크립팅", aliases=["Cross-Site Scripting", "스크립트 삽입 공격"],
         expansion="Cross-Site Scripting",
         expansion_ko="사이트를 넘나드는 스크립트 → 남의 스크립트가 내 페이지에서 실행되는 공격",
         pronunciation={"ko": "엑스에스에스", "read_as": "letters", "note": "CSS와 헷갈리지 않게 X로 줄여 씁니다"},
         stage="secure", level=3,
         definition="공격자가 넣은 글에 숨긴 코드가 다른 사용자의 브라우저에서 실행되게 하는 공격입니다. 화면에 글을 넣을 때 코드로 해석되지 않게 막아서 예방합니다.",
         analogy="게시판 쪽지에 '이 쪽지를 읽는 사람은 지갑을 두고 가시오'라는 주문이 적혀 있고, 읽는 사람이 그대로 따르는 것.",
         pitfall="사용자 입력을 화면에 넣을 때 HTML로 해석되는 방식(innerHTML 등)을 쓰면 뚫립니다. 글자로만 넣는 방식을 기본으로 씁니다.",
         interview_q="화면에 데이터를 넣을 때 XSS를 어떻게 막았나요?",
         interview_a="화면 요소를 만드는 작은 도우미 함수를 하나 두고, 글자는 항상 textContent로만 넣게 했습니다. 그래서 데이터에 이상한 코드가 섞여 있어도 글자로만 보이고 실행되지 않습니다. 화면 코드 전체가 이 함수를 거치게 해서 실수할 자리를 줄였습니다.",
         examples=ex(("meeting", "검색어를 그대로 화면에 다시 보여 주는 기능은 XSS 점검을 꼭 하고 열겠습니다."),
                     ("review", "innerHTML로 사용자 이름을 넣고 있어요. XSS 위험이 있으니 textContent로 바꿔 주세요.")),
         tags=["보안", "화면"], related=["validation", "defense-in-depth"], sources=P("면접 문서: 보안 질문")),

    dict(id="supply-chain-attack", term_en="Supply Chain Attack", term_ko="공급망 공격", aliases=["서플라이 체인 어택", "소프트웨어 공급망 공격", "의존성 공격"],
         pronunciation={"ko": "서플라이 체인 어택", "read_as": "word", "note": "회의에서는 '공급망 공격'이라고 더 자주 말합니다"},
         stage="secure", level=3,
         definition="내 코드가 아니라, 내가 가져다 쓰는 라이브러리나 외부 스크립트에 악성 코드를 넣어 함께 퍼뜨리는 공격입니다.",
         analogy="식당이 아니라 식당에 재료를 대는 납품 업체를 오염시켜, 그 재료를 쓰는 모든 식당에 탈이 나게 하는 것.",
         pitfall="편하다고 출처를 모르는 라이브러리나 외부 서버의 스크립트를 마구 불러오면, 그 업체가 뚫릴 때 나도 함께 뚫립니다. 꼭 필요한 것만 쓰고 버전을 고정하고 보안 알림을 켭니다.",
         interview_q="외부 라이브러리를 쓸 때 보안 위험을 어떻게 줄이나요?",
         interview_a="먼저 꼭 필요한지 따집니다. 학습 앱은 화면에 외부 라이브러리를 하나도 쓰지 않았고, 외부 서버의 스크립트를 불러오는지 자동 점검이 검사합니다. 써야 할 때는 버전을 고정하고, 저장소의 의존성 보안 알림을 켜서 문제가 알려지면 바로 알 수 있게 합니다.",
         examples=ex(("meeting", "이 라이브러리는 관리자가 한 명뿐이라 공급망 공격 위험이 있어요. 대안을 같이 보시죠."),
                     ("review", "외부 CDN 스크립트를 버전 없이 불러오고 있어요. 공급망 공격에 대비해 버전을 고정해 주세요.")),
         tags=["보안", "의존성"], related=["library", "least-privilege", "defense-in-depth"], sources=P("면접 문서: 외부 라이브러리를 쓰지 않은 이유")),
]

PAIRS = []

if __name__ == "__main__":
    add(TERMS, PAIRS)
