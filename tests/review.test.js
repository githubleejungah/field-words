// 학습 기록 규칙 시험 (단위 테스트, Unit Test: 작은 부분 하나를 따로 떼어 확인하는 시험)
// 실행: node --test tests/
const test = require("node:test");
const assert = require("node:assert/strict");
const Review = require("../site/js/review.js");

// 시험마다 빈 저장소와 정해진 날짜로 시작한다
function fresh(date = "2026-11-10") {
  const mem = new Map();
  Review.useStore({ get: (k) => mem.get(k) ?? null, set: (k, v) => mem.set(k, v) });
  const [y, m, d] = date.split("-").map(Number);
  Review.useClock(() => new Date(y, m - 1, d, 9, 0));
  return mem;
}
const setDate = (date) => {
  const [y, m, d] = date.split("-").map(Number);
  Review.useClock(() => new Date(y, m - 1, d, 9, 0));
};

test("5단계 상태: 확신도 × 정답", () => {
  assert.equal(Review.classify("sure", true), "known");
  assert.equal(Review.classify("sure", false), "misconception");
  assert.equal(Review.classify("unsure", true), "shaky");
  assert.equal(Review.classify("unsure", false), "confused");
  assert.equal(Review.classify("dontknow", false), "unknown");
});

test("상자 이동: 앎은 한 칸 올림, 장기 기억(8)에서 멈춤", () => {
  assert.equal(Review.nextBox(0, "known"), 1);
  assert.equal(Review.nextBox(7, "known"), 8);
  assert.equal(Review.nextBox(8, "known"), 8);
});

test("상자 이동: 불안한 앎은 그대로, 틀리면 1번 / 상자 4 이상이면 두 칸만", () => {
  assert.equal(Review.nextBox(3, "shaky"), 3);
  assert.equal(Review.nextBox(0, "shaky"), 1);
  assert.equal(Review.nextBox(3, "confused"), 1);
  assert.equal(Review.nextBox(5, "misconception"), 3);
  assert.equal(Review.nextBox(8, "unknown"), 6);
});

test("복습 간격: 1·2·4·7·15·30·60일, 장기 기억 120일", () => {
  assert.deepEqual([1, 2, 3, 4, 5, 6, 7, 8].map(Review.intervalFor), [1, 2, 4, 7, 15, 30, 60, 120]);
});

test("기록: 처음 맞히면 상자 1, 다음 복습은 내일", () => {
  fresh();
  const r = Review.record("webhook", { confidence: "sure", correct: true });
  assert.equal(r.status, "known");
  assert.equal(r.record.box, 1);
  assert.equal(r.record.next_review_at, "2026-11-11");
  assert.equal(r.firstToday, true);
});

test("오늘 기록: 틀렸다가 다시 맞히면 '바로잡은 것'", () => {
  fresh();
  Review.record("oauth", { confidence: "sure", correct: false });
  let t = Review.getToday();
  assert.deepEqual(t.misconceptions, ["oauth"]);
  const again = Review.record("oauth", { confidence: "unsure", correct: true });
  assert.equal(again.firstToday, false);              // 같은 날 두 번째는 목표 개수에 다시 세지 않음
  t = Review.getToday();
  assert.deepEqual(t.corrected, ["oauth"]);
  assert.equal(t.seen.length, 1);
});

test("장기 기억: 상자 6 이상에서 맞히면 표시", () => {
  const mem = fresh();
  mem.set("fw:v1:review:api", JSON.stringify({ box: 6, lapses: 0, history: [], status: "known" }));
  const r = Review.record("api", { confidence: "sure", correct: true });
  assert.equal(r.record.box, 7);
  assert.equal(r.record.long_term_at, "2026-11-10");
});

test("날짜가 바뀌면 오늘 기록이 새로 시작", () => {
  fresh();
  Review.record("json", { confidence: "sure", correct: true });
  setDate("2026-11-11");
  assert.equal(Review.getToday().seen.length, 0);
});

test("오늘 할 카드: 복습 예정(급한 순) 먼저, 남는 자리에 새 카드, 목표 개수까지", () => {
  const mem = fresh("2026-11-12");
  const terms = ["a", "b", "c", "d", "e"].map((id) => ({ id, stage: "design", level: 2 }));
  mem.set("fw:v1:settings", JSON.stringify({ daily_goal: 3 }));
  mem.set("fw:v1:review:a", JSON.stringify({ box: 2, status: "known", next_review_at: "2026-11-12", history: [], lapses: 0 }));
  mem.set("fw:v1:review:b", JSON.stringify({ box: 1, status: "misconception", next_review_at: "2026-11-12", history: [], lapses: 0 }));
  mem.set("fw:v1:review:c", JSON.stringify({ box: 3, status: "known", next_review_at: "2026-11-20", history: [], lapses: 0 }));
  const p = Review.plan(terms);
  assert.deepEqual(p.queue, ["b", "a", "d"]);          // 착각 b → 복습 a → 새 카드 d (c는 아직 날짜 안 됨)
  assert.equal(p.reviewCount, 2);
  assert.equal(p.newCount, 1);
});

test("확인 문제: 보기 4개, 정답 1개, 혼동 쌍이 오답 보기에 꼭 들어감", () => {
  fresh();
  const terms = ["poc", "mvp", "x1", "x2", "x3", "x4"].map((id) => ({ id, stage: "discovery", level: 3 }));
  const pairs = [{ a: "poc", b: "mvp" }];
  for (let i = 0; i < 20; i++) {
    const q = Review.makeQuiz(terms[0], terms, pairs);
    assert.equal(q.options.length, 4);
    assert.equal(q.options.filter((o) => o.correct).length, 1);
    assert.ok(q.options.some((o) => o.id === "mvp"));
  }
});

test("확인 문제 종류: 상자 3부터는 뜻 → 용어 고르기", () => {
  const mem = fresh();
  const terms = ["t1", "t2", "t3", "t4"].map((id) => ({ id, stage: "build", level: 2 }));
  assert.equal(Review.makeQuiz(terms[0], terms, []).kind, "def");
  mem.set("fw:v1:review:t1", JSON.stringify({ box: 3, history: [], lapses: 0 }));
  assert.equal(Review.makeQuiz(terms[0], terms, []).kind, "term");
});
