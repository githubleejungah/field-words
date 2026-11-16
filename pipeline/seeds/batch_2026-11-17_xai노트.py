"""후보 묶음: X+AI 학습 노트(xai-study-notes, 2026-11-16)에서 고른 새 용어 3개 + 혼동 쌍 1개 (2026-11-17)
- 노트의 용어 26개 중 이미 있는 것(LLM, 에이전트, RAG, 임베딩, SSOT 등 8개)과
  다른 후보 묶음에 있는 것(SSE, 게이트웨이, 라우터, 확신도, BM25, RRF, 시간 제한, 온도, 되묻기, 스트림, 프록시, 포트 12개)은 뺐다.
- 제품 이름(LangGraph, LiteLLM, Azure OpenAI, Vite)은 카드로 만들지 않는다(강의 해설집 검토 때 정한 규칙). 예문 속 맥락으로만 쓴다.
- 노트 문장은 그대로 옮기지 않고 새로 썼다. "현장에선"(field) 예문은 X+AI 챗봇 실습에서 실제로 만든 구조만 적었다(ADR-0005).
검사:  python pipeline/promote.py pipeline/candidates/2026-11-17_xai노트.py --dry-run
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from seedlib import add, ex, src  # noqa: E402

X = lambda: src("planning", "X+AI 심화과정 챗봇 실습 노트 (xai-study-notes, 용어 이름만 참고, 설명은 새로 씀)", "2026-11-16")

TERMS = [
    dict(id="seed-data", term_en="Seed Data", term_ko="시드 데이터", aliases=["초기 데이터", "샘플 데이터", "합성 데이터"],
         pronunciation={"ko": "시드 데이터", "read_as": "word", "ipa": "ˈsid ˌdeɪtə"},
         stage="build", also_stages=["test"], level=2,
         definition="서비스를 처음 띄우거나 시험할 때 미리 넣어 두는 기본 데이터입니다. 빈 화면 대신 바로 써 볼 수 있게 하고, 시험을 늘 같은 조건에서 돌리게 합니다.",
         analogy="새 화분에 처음 심는 씨앗. 이것이 있어야 싹이 어떻게 자라는지 볼 수 있습니다.",
         pitfall="빨리 하려고 실제 고객 데이터를 복사해 시드로 쓰면 개인정보가 시험 환경과 Git에 퍼집니다. 실제와 비슷하게 꾸며 만든 합성 데이터를 씁니다.",
         interview_q="고객 데이터를 받기 전에 데모를 어떻게 준비하겠어요?",
         interview_a="실제와 같은 모양의 합성 시드 데이터를 먼저 만들겠습니다. 고객이 쓰는 항목 이름과 개수, 자주 나오는 예외 상황을 닮게 만들고, 개인정보는 넣지 않습니다. 그러면 데이터가 오기 전에도 흐름을 시연하고 시험을 돌릴 수 있고, 실제 데이터가 오면 모양이 맞는지 바로 비교할 수 있습니다.",
         examples=ex(("meeting", "고객 데이터 반입 승인이 나기 전까지는 시드 데이터로 데모를 준비하겠습니다."),
                     ("review", "시드 데이터에 실제 고객 전화번호가 섞여 있어요. 합성 번호로 바꿔 주세요."),
                     ("field", "X+AI 챗봇 실습에서 상품·프로모션·정책·FAQ를 실제 개인정보 없이 합성 시드 데이터로 만들어 검색과 답변을 시험했다.")),
         tags=["데이터", "개발"], related=["mock-api", "evaluation-dataset", "de-identification"], sources=X()),

    dict(id="orchestrator-workers", term_en="Orchestrator-Workers", term_ko="지휘자-작업자 패턴", aliases=["워커", "Worker", "오케스트레이터-워커", "작업자 에이전트"],
         pronunciation={"ko": "오케스트레이터 워커스", "read_as": "word", "ipa": "ˈɔrkəˌstreɪtər ˈwɝkərz", "note": "회의에서는 '워커'라고 줄여 많이 말합니다"},
         stage="automate", also_stages=["design"], level=3,
         definition="지휘하는 AI가 일을 나눠 분야별 작업자(워커)에게 맡기고, 결과를 모아 하나로 합치는 에이전트 설계 방식입니다. 분야마다 지시와 자료를 따로 두어 정확도를 높입니다.",
         analogy="식당 주방장이 주문을 보고 국은 국 담당, 구이는 구이 담당에게 나눠 맡긴 뒤 한 상으로 차려 내는 것.",
         pitfall="워커를 너무 잘게 나누면 넘기고 합치는 단계마다 시간과 비용이 늘고 오류 지점도 많아집니다. 정말 지시와 자료가 다른 분야만 나눕니다.",
         interview_q="챗봇이 다루는 주제가 여러 개일 때 에이전트를 어떻게 나누겠어요?",
         interview_a="먼저 질문을 분류하는 단계를 두고, 주제마다 지시문과 참고 자료가 다른 워커를 따로 두겠습니다. 지휘하는 쪽은 분류와 결과 합치기만 맡게 해서 각 워커를 따로 시험하고 고칠 수 있게 합니다. 주제가 두세 개뿐이면 나누지 않고 한 에이전트로 시작하는 것이 더 단순하다고 판단합니다.",
         examples=ex(("meeting", "상품 문의와 환불 정책은 참고 자료가 달라서 워커를 둘로 나누겠습니다."),
                     ("review", "지휘 단계에서 워커 결과를 다시 고쳐 쓰고 있어요. 합치기만 하고, 고칠 것은 해당 워커로 돌려보내 주세요."),
                     ("field", "X+AI 챗봇 실습에서 질문을 분류해 상품·프로모션·정책 FAQ·홍보 문구 네 워커 중 하나로 보내도록 설계했다.")),
         tags=["AI", "설계"], related=["ai-agent", "orchestration", "critic-agent"], sources=X()),

    dict(id="critic-agent", term_en="Critic", term_ko="비평가 에이전트", aliases=["critic", "크리틱", "Evaluator-Optimizer", "반성 패턴", "Reflection"],
         pronunciation={"ko": "크리틱", "read_as": "word", "ipa": "ˈkrɪtɪk"},
         stage="automate", also_stages=["test"], level=3,
         definition="다른 AI가 쓴 초안을 검사해서, 근거와 맞지 않거나 빠진 것이 있으면 다시 쓰게 돌려보내는 AI 단계입니다. 답을 내보내기 전에 품질을 한 번 더 걸러 냅니다.",
         analogy="신입이 쓴 보고서를 선배가 한 번 읽고 틀린 곳을 짚어 다시 쓰게 하는 것.",
         pitfall="다시 쓰기 횟수에 한도가 없으면 같은 초안을 끝없이 돌려 시간과 비용이 터집니다. 최대 횟수를 정하고, 넘으면 사람에게 넘기거나 모른다고 답합니다.",
         examples=ex(("meeting", "답에 근거 없는 주장이 섞이지 않게, 내보내기 전에 critic 단계를 하나 두겠습니다."),
                     ("review", "critic이 다시 쓰라고 할 때 횟수 제한이 없어요. 두 번까지만 돌리고 넘기게 해 주세요."),
                     ("field", "X+AI 챗봇 실습에서 critic이 초안의 주장마다 근거 문서와 맞는지 확인하고, 어긋나면 같은 워커에게 최대 2번 다시 쓰게 했다.")),
         tags=["AI", "품질"], related=["orchestrator-workers", "llm-as-a-judge", "guardrail", "hallucination"], sources=X()),
]

PAIRS = [
    dict(id="critic-agent-vs-llm-as-a-judge", a="critic-agent", b="llm-as-a-judge",
         difference="critic은 답을 만드는 흐름 안에서 초안을 검사해 다시 쓰게 하고, LLM 심사관은 다 만든 결과를 기준표로 채점해 품질을 잽니다."),
]

if __name__ == "__main__":
    add(TERMS, PAIRS)
