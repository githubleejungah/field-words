"""후보 묶음: 리테일 챗봇 실습(2026-11-15) 용어 1차 — 새 카드 10개 + 혼동 쌍 1개 (2026-11-16 작성)
- 출처: field-words-inbox 이슈 1번 "[용어후보] 리테일 챗봇 실습 세션 · 2026-11-15"의 "1차로 먼저 다듬을 15개".
- 15개 중 5개는 승인 대기 후보에 이미 카드가 있어 새로 만들지 않았다. 대신 그 카드에 '현장에선' 예시·출처를 더했다.
    sse, hybrid-search → 2026-11-13_강의1회차.py
    fallback, rrf(=reciprocal-rank-fusion), intent-routing(=query-routing, 별칭 '의도 라우팅' 추가) → 2026-11-14_강의2회차.py
- 기존 122개, 승인 대기 83개(서버인프라 20 · 강의1회차 30 · 강의2회차 33)와 id가 겹치지 않는다.
- 이슈의 '나온 상황 한 줄'은 실제 겪은 일이라 예문 상황 field(화면 이름 '현장에선')로 넣었다 (ADR-0005, 스키마 1.1).
  회의·리뷰·면접 예문은 연습용으로 새로 썼다. 면접 답은 해 보지 않은 일을 해 본 것처럼 쓰지 않는다 → "이렇게 하겠습니다".
- 혼동 쌍은 이미 공개된 용어나 이 묶음 안의 용어끼리만 묶었다(bm25 ↔ embedding). 이슈 메모의 다른 짝은
  SSE ↔ WebSocket(강의1회차에 이미 있음), hook ↔ webhook · liveness ↔ startup probe · SLO ↔ SLA(2차 이후 용어)라 이번에 넣지 않았다.
- 확인 필요: bm25의 현업 발음('비엠 이십오' / '비엠 투엔티파이브'), sources 종류를 lecture로 둔 것.
검사:  python pipeline/promote.py pipeline/candidates/2026-11-15_리테일챗봇_1차.py --dry-run
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from seedlib import add, ex, src  # noqa: E402

RC = lambda: src("lecture", "리테일 챗봇 실습 (매치업 X+AI 심화과정 1주차) 2026-11-15 — 실제 겪은 상황, 설명은 새로 씀", "2026-11-15")

TERMS = [
    # ================= 통신·연결 =================
    # 근거: MDN 'Streams API', OpenAI·Anthropic API 문서의 stream 옵션(토큰을 생성되는 대로 전송)
    dict(id="streaming", term_en="Streaming", term_ko="스트리밍 (조각 전송)",
         aliases=["스트리밍", "스트리밍 응답", "토큰 스트리밍", "stream"],
         pronunciation={"ko": "스트리밍", "read_as": "word", "ipa": "ˈstrimɪŋ"},
         stage="build", also_stages=["design"], level=2,
         definition="결과를 다 만든 뒤 한꺼번에 보내지 않고, 만들어지는 조각부터 바로바로 보내는 방식입니다. LLM 답을 토큰 단위로 흘려보내면 사용자가 첫 글자를 빨리 보고 기다림을 덜 느낍니다.",
         analogy="코스 요리를 한 접시씩 내 주는 것. 마지막 요리가 끝날 때까지 손님을 굶기지 않습니다.",
         pitfall="중간에 연결이 끊기면 반쪽 답이 화면에 남습니다. 끝 신호와 오류 신호를 따로 보내고, 화면은 끝 신호를 받아야 완료로 표시해야 합니다.",
         interview_q="LLM 답을 스트리밍으로 보내면 무엇이 좋아지고, 무엇이 어려워지나요?",
         interview_a="스트리밍은 답 전체를 기다리지 않고 토큰이 만들어지는 대로 보내서, 사용자가 첫 글자를 빨리 봅니다. 대신 중간에 끊겼을 때의 처리, 이미 보낸 글을 고칠 수 없다는 점, 로그를 조각으로 모아야 한다는 점이 어려워집니다. 그래서 끝 신호와 오류 신호를 정하고 첫 토큰까지 시간을 따로 재겠습니다.",
         examples=ex(("meeting", "답 생성이 10초 넘게 걸리니 스트리밍으로 바꿔 첫 글자부터 보여 드리겠습니다."),
                     ("review", "스트리밍 도중 오류가 나면 화면이 계속 로딩 중이에요. 오류 이벤트를 받으면 멈추게 해 주세요."),
                     ("field", "리테일 챗봇 실습에서 답을 다 만들기 전에 토큰 조각부터 스트리밍으로 보내 첫 글자를 빨리 띄웠습니다.")),
         tags=["AI", "통신"], related=["sse", "ttft", "llm", "websocket"], sources=RC()),

    # 근거: IETF RFC 6335(포트 번호 관리), MDN 'Port' 용어집
    dict(id="port", term_en="Port", term_ko="포트",
         aliases=["포트 번호", "포트번호", "port number"],
         pronunciation={"ko": "포트", "read_as": "word", "ipa": "pɔrt"},
         stage="build", also_stages=["deploy", "operate"], level=2,
         definition="한 컴퓨터 안에서 여러 프로그램이 각자 요청을 받을 수 있게 나눠 둔 번호입니다. 같은 PC에서 화면, 게이트웨이, 서버를 서로 다른 포트로 동시에 띄워 구분하려고 씁니다.",
         analogy="아파트 주소는 같아도 동·호수로 집을 구분하는 것.",
         pitfall="다른 프로그램이 이미 쓰는 포트로 띄우면 '이미 사용 중' 오류로 시작하지 못합니다. 개발용 포트를 열어 둔 채 배포하면 외부에 그대로 드러납니다.",
         interview_q="로컬에서 '포트가 이미 사용 중'이라는 오류가 나면 어떻게 해결하나요?",
         interview_a="같은 포트를 다른 프로그램이 쓰고 있다는 뜻입니다. 먼저 어떤 프로세스가 그 포트를 잡고 있는지 확인해, 필요 없으면 끄고 아니면 설정에서 포트를 바꾸겠습니다. 포트를 바꾸면 그 주소를 부르는 프록시와 환경 변수도 함께 고치겠습니다.",
         examples=ex(("meeting", "로컬에서는 화면을 5173, 게이트웨이를 18080 포트로 띄우니 두 주소를 구분해 주세요."),
                     ("review", "포트 번호가 코드에 그대로 박혀 있어요. 환경 변수로 빼 주세요."),
                     ("field", "리테일 챗봇 실습에서 화면 5173, 게이트웨이 18080, 에이전트 8000 포트가 각각 무엇인지 하나씩 짚어 봤습니다.")),
         tags=["네트워크", "개발 환경"], related=["proxy", "environment-variable", "api"], sources=RC()),

    # 근거: MDN 'Proxy servers and tunneling', Vite 문서 'server.proxy'(개발 서버에서만 동작)
    dict(id="proxy", term_en="Proxy", term_ko="프록시",
         aliases=["프록시 서버", "대리 서버", "개발 서버 프록시"],
         pronunciation={"ko": "프록시", "read_as": "word", "ipa": "ˈprɑksi"},
         stage="build", also_stages=["deploy", "secure"], level=2,
         definition="요청을 중간에서 대신 받아 실제 서버로 넘겨 주고, 답을 다시 돌려주는 중간 다리입니다. 주소를 하나로 모으거나, 보안 검사·캐시를 중간에 두려고 씁니다.",
         analogy="비서가 전화를 대신 받아 담당자에게 돌려 주는 것.",
         pitfall="개발 서버의 프록시 설정은 배포하면 따라가지 않습니다. 로컬에서 잘 되던 /api 호출이 운영에서 404나 CORS 오류가 나면, 운영 쪽에 같은 경로 연결이 있는지부터 봐야 합니다.",
         interview_q="개발 서버 프록시를 쓰면 왜 CORS 오류가 나지 않나요?",
         interview_a="브라우저는 화면과 같은 주소로 요청을 보내고, 개발 서버가 그 요청을 뒤에서 백엔드로 넘겨 줍니다. 브라우저 입장에서는 다른 출처로 요청한 적이 없으니 CORS 검사가 일어나지 않습니다. 이 설정은 개발용이라, 운영에서는 게이트웨이나 웹 서버에 같은 경로 연결을 따로 두겠습니다.",
         examples=ex(("meeting", "로컬에서는 개발 서버 프록시가 /api 요청을 게이트웨이로 넘기니, 화면 코드에 서버 주소를 적지 않겠습니다."),
                     ("review", "vite.config의 프록시가 예전 포트를 가리켜요. 게이트웨이 포트로 바꿔 주세요."),
                     ("field", "리테일 챗봇 실습에서 Vite 개발 서버의 프록시가 /api 요청을 18080 게이트웨이로 넘겨 주는 것을 확인했습니다.")),
         tags=["네트워크", "개발 환경"], related=["port", "cors", "api", "cache"], sources=RC()),

    # 근거: MDN 'Cross-Origin Resource Sharing (CORS)', WHATWG Fetch 표준(CORS 프로토콜). 브라우저가 지키는 규칙
    dict(id="cors", term_en="CORS", term_ko="교차 출처 리소스 공유",
         aliases=["코스", "CORS 오류", "교차 출처", "Cross-Origin"],
         expansion="Cross-Origin Resource Sharing",
         expansion_ko="Cross-Origin(다른 출처 사이의) Resource(자원) Sharing(공유) → 교차 출처 리소스 공유",
         pronunciation={"ko": "코스", "read_as": "word", "ipa": "kɔrz", "variants": ["씨오알에스"],
                        "note": "'코스'와 글자로 읽는 '씨오알에스'를 둘 다 씁니다"},
         stage="build", also_stages=["secure"], level=3,
         definition="브라우저는 원래 다른 출처(주소·포트·프로토콜 중 하나라도 다른 곳)의 응답을 화면 코드가 읽지 못하게 막는데, 서버가 응답 헤더로 허락하면 읽게 해 주는 규칙입니다. 안전을 지키면서 필요한 출처끼리만 데이터를 주고받으려고 씁니다.",
         analogy="다른 회사 건물에 들어갈 때, 그 회사 방문자 명단에 있는 사람만 들여보내는 것.",
         pitfall="오류를 없애려고 허용 출처를 *(모두)로 열거나 요청한 출처를 그대로 허락하면, 아무 사이트에서나 이 API를 불러 결과를 읽을 수 있습니다. 허용할 출처를 목록으로 정해야 합니다.",
         interview_q="Postman에서는 되는데 브라우저에서만 CORS 오류가 나는 이유는 무엇인가요?",
         interview_a="CORS는 서버가 아니라 브라우저가 지키는 규칙이라서, Postman이나 curl은 검사하지 않습니다. 브라우저는 다른 출처로 요청할 때 서버의 허용 헤더를 확인하고, 없으면 응답을 화면 코드에 넘기지 않습니다. 그래서 서버에 허용할 출처를 정확히 적거나, 같은 출처로 보이게 프록시를 두겠습니다.",
         examples=ex(("meeting", "화면과 API 주소가 달라서 CORS 허용 목록에 운영 화면 주소만 넣겠습니다."),
                     ("review", "CORS 허용 출처가 *로 열려 있어요. 실제 화면 주소만 적어 주세요."),
                     ("field", "리테일 챗봇 실습에서 화면과 API 포트가 달라도 프록시를 거치면 CORS에 막히지 않는 이유를 정리했습니다.")),
         tags=["보안", "네트워크", "웹"], related=["proxy", "port", "xss", "api"], prerequisites=["port"], sources=RC()),

    # 근거: MDN 'AbortSignal.timeout()', AWS Builders' Library 'Timeouts, retries, and backoff with jitter'
    dict(id="timeout", term_en="Timeout", term_ko="타임아웃",
         aliases=["시간 초과", "제한 시간", "타임 아웃", "time out"],
         pronunciation={"ko": "타임아웃", "read_as": "word", "ipa": "ˈtaɪmˌaʊt"},
         stage="build", also_stages=["operate"], level=2,
         definition="응답을 기다리는 최대 시간을 정해 두고, 넘으면 기다리기를 멈추고 실패로 처리하는 설정입니다. 느린 상대 때문에 우리 서비스까지 멈춰 버리는 것을 막으려고 씁니다.",
         analogy="약속 시간에서 30분이 지나도 안 오면 더 기다리지 않고 먼저 가는 것.",
         pitfall="여러 단계로 이어진 호출에서 안쪽 제한이 바깥보다 길면, 바깥이 먼저 끊어 버려 안쪽 결과는 버려지고 원인도 남지 않습니다. 안쪽 제한을 바깥보다 짧게 잡아야 합니다.",
         interview_q="화면 → 게이트웨이 → 에이전트 → LLM으로 이어진 호출에서 타임아웃을 어떻게 정하겠습니까?",
         interview_a="바깥에서 안쪽으로 갈수록 타임아웃을 짧게 잡겠습니다. 그래야 안쪽이 먼저 실패를 알리고, 바깥은 그 이유를 받아 사용자에게 전할 수 있습니다. LLM처럼 첫 응답이 느린 구간은 첫 토큰까지 시간과 전체 시간을 따로 재서 정하겠습니다.",
         examples=ex(("meeting", "결제 API는 타임아웃을 5초로 두고, 넘으면 잠시 후 다시 시도하라는 안내를 보여 드리겠습니다."),
                     ("review", "게이트웨이 타임아웃이 에이전트보다 짧아요. 안쪽 제한이 바깥보다 짧도록 맞춰 주세요."),
                     ("field", "리테일 챗봇 실습에서 채팅 TIMEOUT 원인을 찾다가 '안쪽 제한이 바깥보다 짧아야 한다'는 규칙을 정리했습니다.")),
         tags=["운영", "통신", "안정성"], related=["ttft", "fallback", "rate-limit", "monitoring"], sources=RC()),

    # ================= LLM 응답·분류 =================
    # 근거: NVIDIA NIM 'LLM inference benchmarking: metrics'(TTFT 정의), vLLM 벤치마크 지표. 표준 기관 정의 없음
    dict(id="ttft", term_en="Time To First Token", term_ko="첫 토큰까지 시간",
         aliases=["TTFT", "티티에프티", "첫 토큰 시간", "첫 응답 시간"],
         expansion="Time To First Token",
         expansion_ko="Time(시간) To First(첫) Token(토큰) → 첫 토큰까지 걸리는 시간",
         pronunciation={"ko": "티티에프티", "read_as": "letters", "ipa": "ˌtiˌtiˌɛfˈti", "tts": "T T F T"},
         stage="operate", also_stages=["test", "build"], level=3,
         definition="요청을 보낸 뒤 LLM의 첫 토큰(답의 첫 조각)이 도착할 때까지 걸린 시간입니다. 스트리밍 서비스에서 사용자가 '반응이 빠르다'고 느끼는지를 재려고 씁니다.",
         analogy="식당에서 주문한 뒤 첫 반찬이 나오기까지 걸린 시간.",
         pitfall="전체 응답 시간만 보면 첫 글자가 30초 뒤에 나와도 평균에 묻혀 모릅니다. 첫 이벤트 제한 시간을 TTFT보다 짧게 잡으면 정상 응답도 타임아웃으로 끊깁니다.",
         interview_q="LLM 응답 속도를 볼 때 TTFT와 전체 응답 시간을 왜 나눠서 보나요?",
         interview_a="TTFT는 사용자가 기다림을 느끼는 시간이고, 전체 응답 시간은 답이 끝날 때까지의 시간입니다. 스트리밍이면 전체가 길어도 첫 토큰이 빠르면 덜 답답하게 느낍니다. 그래서 두 값을 따로 재고, 타임아웃도 첫 이벤트용과 전체용으로 나눠 정하겠습니다.",
         examples=ex(("meeting", "추론 모델로 바꾸면 TTFT가 늘어나니, 생각 중이라는 안내를 먼저 보여 드리겠습니다."),
                     ("review", "대시보드에 평균 응답 시간만 있어요. TTFT를 따로 기록해 주세요."),
                     ("field", "리테일 챗봇 실습에서 TTFT가 30초 가까이 걸려, 첫 이벤트를 기다리는 제한을 60초로 늘렸습니다.")),
         tags=["AI", "성능"], related=["streaming", "timeout", "llm", "monitoring"], sources=RC()),

    # 근거: Google ML Crash Course 'Classification: thresholds', Guo et al. 2017 'On Calibration of Modern Neural Networks'(확신도와 실제 정답률 불일치)
    dict(id="confidence-score", term_en="Confidence Score", term_ko="확신도 점수",
         aliases=["확신도", "신뢰도 점수", "컨피던스", "confidence"],
         pronunciation={"ko": "컨피던스 스코어", "read_as": "word", "ipa": "ˈkɑnfɪdəns skɔr"},
         stage="build", also_stages=["test"], level=3,
         definition="모델이 자기 판단을 얼마나 확신하는지 0~1 사이 숫자로 나타낸 값입니다. 확신이 낮을 때 바로 답하지 않고 되묻거나 사람에게 넘기는 기준으로 씁니다.",
         analogy="일기 예보의 '비 올 확률 90%'.",
         pitfall="모델이 말한 확신도가 실제로 맞힐 확률과 같다는 보장은 없습니다. 특히 LLM이 글로 답한 숫자는 그럴듯하게 지어낸 값일 수 있어, 기준값(예: 0.6)은 평가 데이터로 맞춰 봐야 합니다.",
         interview_q="LLM이 답한 확신도 0.9를 그대로 믿어도 되나요?",
         interview_a="그대로 믿지 않겠습니다. LLM이 말한 확신도는 실제 정답률과 어긋날 수 있습니다. 평가 데이터에서 확신도 구간별로 실제 정답률을 재 보고, 그 결과로 되묻기나 사람 확인으로 넘길 기준값을 정하겠습니다.",
         examples=ex(("meeting", "확신도 점수가 0.6보다 낮은 질문은 상담원에게 넘기겠습니다."),
                     ("review", "확신도 기준 0.6을 정한 근거가 없어요. 평가셋 결과를 함께 적어 주세요."),
                     ("field", "리테일 챗봇 실습에서 작은 모델이 '정책 FAQ 0.9, 상품 추천 0.05'라고 답한 확신도 점수를 어떻게 읽을지 따져 봤습니다.")),
         tags=["AI", "평가"], related=["clarifying-question", "evaluation-dataset", "human-in-the-loop", "hallucination"], sources=RC()),

    # 근거: Microsoft Learn 'Conversational language understanding' 모호한 의도 처리, 대화 설계 실무 관례. 표준 정의 없음
    dict(id="clarifying-question", term_en="Clarifying Question", term_ko="되묻기 질문",
         aliases=["되묻기", "명확화 질문", "확인 질문", "재질문"],
         pronunciation={"ko": "클래리파잉 퀘스천", "read_as": "word", "ipa": "ˈklɛrəˌfaɪɪŋ ˈkwɛstʃən"},
         stage="design", also_stages=["build"], level=3,
         definition="질문이 애매해 어느 쪽으로 답할지 확실하지 않을 때, 추측해서 답하지 않고 사용자에게 다시 물어 뜻을 좁히는 질문입니다. 엉뚱한 답을 내는 것보다 한 번 묻는 편이 빠르고 정확할 때 씁니다.",
         analogy="점원이 '아이스로 드릴까요, 따뜻하게 드릴까요?' 하고 확인하는 것.",
         pitfall="너무 자주 되물으면 사용자가 지쳐 떠납니다. 1·2위 후보의 확신도 차이가 작을 때처럼 되묻는 조건을 숫자로 정하고, 고를 보기 2~3개를 함께 보여 줘야 합니다.",
         interview_q="챗봇이 언제 되묻기 질문을 하게 설계하겠습니까?",
         interview_a="의도 분류에서 1위와 2위 확신도 차이가 작거나, 답에 꼭 필요한 정보가 빠졌을 때만 되묻겠습니다. 이때 '배송 문의인가요, 반품 문의인가요?'처럼 고를 수 있는 보기를 함께 주겠습니다. 되묻기 비율과 그 뒤 해결률을 재서 조건을 조정하겠습니다.",
         examples=ex(("meeting", "의도가 둘로 갈리면 바로 답하지 않고 되묻기 질문으로 확인하겠습니다."),
                     ("review", "되묻기 질문이 거의 매번 나와요. 1·2위 확신도 차이 기준을 추가해 주세요."),
                     ("field", "리테일 챗봇 실습에서 1·2위 확신도 차이가 작으면 사용자에게 되묻기 질문을 하도록 정했습니다.")),
         tags=["AI", "대화 설계"], related=["confidence-score", "human-in-the-loop", "requirements"], sources=RC()),

    # 근거: OpenAI API Reference 'temperature', OpenAI 'Reasoning models' 문서(추론 모델은 일부 샘플링 설정 미지원)
    dict(id="temperature", term_en="Temperature", term_ko="온도 (답의 다양성)",
         aliases=["템퍼러처", "온도", "temp", "샘플링 온도"],
         pronunciation={"ko": "템퍼러처", "read_as": "word", "ipa": "ˈtɛmpərətʃɚ"},
         stage="build", also_stages=["test"], level=2,
         definition="LLM이 다음 단어를 고를 때 가장 그럴듯한 쪽만 고를지, 다른 후보도 섞어 고를지 정하는 설정값입니다. 낮으면 같은 질문에 비슷한 답이, 높으면 다양한 답이 나와서, 분류처럼 일관성이 필요한 일에는 낮게 둡니다.",
         analogy="요리사에게 '레시피대로'와 '오늘은 마음대로' 사이를 고르게 하는 다이얼.",
         pitfall="온도는 답의 다양성을 바꿀 뿐 정확도나 성능을 올려 주지 않습니다. 일부 추론 모델은 온도를 바꿀 수 없어서, 값을 보내면 요청 자체가 거부됩니다.",
         interview_q="의도 분류에는 온도를 어떻게 두고, 그 이유는 무엇인가요?",
         interview_a="의도 분류는 같은 질문에 같은 결과가 나와야 하니 온도를 낮게 두겠습니다. 다만 온도가 0이어도 결과가 완전히 같다고 보장되지는 않아서, 평가 데이터로 여러 번 돌려 흔들림을 확인하겠습니다. 온도를 지원하지 않는 모델이면 설정을 빼고 프롬프트와 출력 형식으로 일관성을 잡겠습니다.",
         examples=ex(("meeting", "홍보 문구는 다양해야 하니 온도를 높이고, 질문 분류는 낮게 두겠습니다."),
                     ("review", "이 모델은 temperature를 지원하지 않아 요청이 실패해요. 모델별로 설정을 빼 주세요."),
                     ("field", "리테일 챗봇 실습에서 gpt-5-mini가 temperature 0을 거부해 설정을 빼야 했습니다.")),
         tags=["AI", "설정"], related=["llm", "prompt", "hallucination"], sources=RC()),

    # ================= 검색 =================
    # 근거: Robertson & Zaragoza 2009 'The Probabilistic Relevance Framework: BM25 and Beyond', Elasticsearch 문서 'Similarity module'(기본값 BM25)
    dict(id="bm25", term_en="BM25", term_ko="BM25 (키워드 검색 점수)",
         aliases=["Okapi BM25", "비엠25", "키워드 검색 점수"],
         expansion="Best Matching 25",
         expansion_ko="Best(가장) Matching(잘 맞는) 25(25번째 공식) → 가장 잘 맞는 문서를 고르는 25번째 점수 공식",
         pronunciation={"ko": "비엠 이십오", "read_as": "mixed", "ipa": "ˌbiˈɛm ˌtwɛntiˈfaɪv", "tts": "B M 25",
                        "variants": ["비엠 투엔티파이브"], "note": "'비엠 이십오'와 '비엠 투엔티파이브'를 둘 다 씁니다"},
         stage="build", also_stages=["test"], level=3,
         definition="검색어 단어가 문서에 얼마나 자주 나오는지, 전체 문서 중에서 얼마나 드문 단어인지, 문서가 얼마나 긴지를 함께 따져 키워드 검색 점수를 매기는 공식입니다. Elasticsearch 같은 검색 엔진의 기본 점수 방식이라, 정확한 단어가 중요한 검색에 씁니다.",
         analogy="책 색인에서 찾는 단어가 많이 나오면서도, 흔한 말이 아닌 페이지에 점수를 더 주는 것.",
         pitfall="BM25는 글자가 같아야 점수를 줍니다. '환불'로 물었는데 문서에 '반품 비용 돌려받기'라고만 있으면 못 찾습니다. 뜻으로 찾는 임베딩 검색과 함께 쓰는 이유입니다.",
         interview_q="RAG에서 BM25와 임베딩 검색을 함께 쓰는 이유는 무엇인가요?",
         interview_a="BM25는 상품 코드나 고유 이름처럼 정확한 단어가 맞을 때 강하고, 임베딩 검색은 표현이 달라도 뜻이 비슷하면 찾습니다. 서로 약한 곳을 메워 주므로 두 결과를 합치는 하이브리드 검색을 씁니다. 합칠 때는 점수 단위가 달라 순위 기반으로 섞겠습니다.",
         examples=ex(("meeting", "상품 코드 검색은 BM25가 정확하니 키워드 검색을 꼭 함께 두겠습니다."),
                     ("review", "BM25 점수와 벡터 점수를 그대로 더하고 있어요. 단위가 다르니 순위로 합쳐 주세요."),
                     ("field", "리테일 챗봇 실습에서 Elasticsearch 키워드 검색 결과마다 붙은 BM25 점수를 하나씩 확인했습니다.")),
         tags=["검색", "AI"], related=["embedding", "vector-db", "hybrid-search", "reciprocal-rank-fusion", "rag"], sources=RC()),
]

PAIRS = [
    # 기준: 둘 다 'RAG 검색 방식'으로 함께 소개되고, 하이브리드 검색에서 나란히 나와 섞어 부르기 쉽다. 차이는 '글자 일치 vs 뜻 가까움'
    dict(id="bm25-vs-embedding", a="bm25", b="embedding",
         difference="BM25는 검색어와 같은 글자가 문서에 얼마나 나오는지로 점수를 매기고, 임베딩은 글의 뜻을 숫자 벡터로 바꿔 뜻이 가까운 문서를 찾게 합니다."),
]

if __name__ == "__main__":
    add(TERMS, PAIRS)
