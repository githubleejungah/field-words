/* =========================================================
   필드워드 v0.1 — 목록 · 검색 · 용어 카드(모드 3개) · 듣기
   프레임워크 없이 브라우저 기본 기능(DOM, fetch, Web Speech API)만 쓴다.

   화면은 3개뿐이다.
     #/              목록 (검색, 단계 고르기)
     #/term/<id>     용어 카드 — 모드 전환 막대로 👀 보기 / 🚶 이동 중 / 🗣️ 말하기를 고른다
     #/about         정보
   ========================================================= */

const APP_VERSION = "0.1.0";

// 단계 순서 (프로젝트 지도). 화면의 단계 버튼이 이 순서로 나온다.
const STAGES = ["discovery", "design", "build", "test", "deploy", "operate", "secure", "grow", "automate"];

// 학습 모드. 같은 카드 화면에서 바꾼다. 바꾼 모드는 이번 학습 동안만 유지된다(새로고침하면 보기로).
//   look  👀 보기:    소리 없이 보고, 원할 때 듣는다. 직접 넘긴다.
//   walk  🚶 이동 중: 카드를 열면 자동으로 전부 읽고, 2초 뒤 다음 카드로 넘어간다. 화면을 켜 둔다.
//   speak 🗣️ 말하기:  용어만 듣고 소리 내어 설명해 본다. (채점은 다음 업데이트)
const MODES = ["look", "walk", "speak"];
const NEXT_CARD_DELAY_MS = 2000;

// 의견 보내기 설정
// - accessKey: Web3Forms(무료 양식 전송 서비스)에서 받은 키. 넣으면 앱 안에서 바로 전송되고 받는 메일로 도착한다.
//   이 키는 공개돼도 괜찮게 설계된 값이라 코드에 둬도 된다. 받는 이메일 주소는 Web3Forms 쪽에만 저장된다.
// - mailto: 키가 아직 없을 때 쓰는 대신 방법. 사용자의 메일 앱을 열어 내용을 채워 준다.
const FEEDBACK = {
  accessKey: "",
  endpoint: "https://api.web3forms.com/submit",
  mailto: "veryfar4@gmail.com",   // 의견을 받는 메일 (2026-11-10 사용자 지정)
};

// 앱이 기억하는 값(상태, State)을 한곳에 모은다.
const state = {
  terms: [],          // 공개 중인 용어 (대체된 용어 제외)
  allById: new Map(), // id → 용어 (대체된 용어 포함. 옛 링크를 새 용어로 보내기 위해)
  pairs: [],          // 혼동 쌍
  text: {},           // 화면 문구 (i18n/ko.json)
  query: "",          // 검색어
  stage: "all",       // 고른 단계
  mode: "look",       // 학습 모드
  nextTimer: null,    // 이동 중 모드: 다음 카드로 넘어가기 전 2초 기다리는 타이머
  hold: false,        // true면 다음 카드를 열 때 자동으로 읽지 않는다 (사용자가 멈춘 채로 넘겼을 때)
  session: null,      // 오늘의 학습 진행 중: { queue: [용어 id], i: 지금 몇 번째, retries: {id: 다시 나온 횟수} }
  extraGoal: 0,       // 오늘 목표를 채운 뒤 "더 하기"로 늘린 장 수 (오늘만)
  celebratedTier: 0,  // 오늘 이미 축하한 칭찬 단계 (같은 단계는 한 번만 축하)
};

const app = document.getElementById("app");
const topbar = document.getElementById("topbar");

/* ---------- 작은 도구들 ---------- */

// 화면 문구 가져오기. {n} 같은 자리는 값으로 바꾼다.
function t(key, vars = {}) {
  let s = state.text[key] ?? key;
  for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, v);
  return s;
}

// 요소 만들기 도우미. 글자는 textContent로만 넣는다.
// (innerHTML에 글자를 그대로 넣으면 데이터 속 <script>가 실행될 수 있다: XSS 방지)
function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c === undefined || c === null || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

// 검색용으로 글자를 고르게 만든다: 소문자로, 띄어쓰기·하이픈·점 없애기
// 예: "Web Hook", "web-hook", "웹 훅" → "webhook", "웹훅"
function normalize(s) {
  return String(s).toLowerCase().replace(/[\s\-_.·/]/g, "");
}

/* ---------- 데이터 불러오기 ---------- */

async function loadData() {
  // cache: "no-cache" — 저장해 둔 파일이 있어도 서버에 "바뀌었나요?"를 먼저 묻는다. 용어가 추가되면 바로 보이게.
  const [glossary, text] = await Promise.all([
    fetch("data/glossary.json", { cache: "no-cache" }).then((r) => r.json()),
    fetch("i18n/ko.json", { cache: "no-cache" }).then((r) => r.json()),
  ]);
  state.text = text;
  state.pairs = glossary.confusable_pairs;
  for (const term of glossary.terms) state.allById.set(term.id, term);
  state.terms = glossary.terms.filter((term) => !term.replaced_by);
  // 날짜별 일지가 생기기 전에 공부한 기록을 한 번만 되살린다 (2026-11-11 추가)
  Review.ensureLog([...state.allById.keys()]);
}

/* ---------- 검색 ---------- */

// 검색어가 들어 있는 용어를 찾고, 더 잘 맞는 것을 앞에 둔다.
function searchTerms() {
  const q = normalize(state.query);
  const inStage = (term) => state.stage === "all" || term.stage === state.stage;

  const results = [];
  for (const term of state.terms) {
    if (!inStage(term)) continue;
    if (!q) { results.push({ term, score: 0 }); continue; }

    const names = [term.term_en, term.term_ko, ...(term.aliases ?? [])].map(normalize);
    const extra = [term.expansion ?? "", term.pronunciation.ko].map(normalize);

    let score = -1;
    if (names.some((n) => n === q)) score = 3;            // 이름과 똑같음
    else if (names.some((n) => n.startsWith(q))) score = 2; // 이름이 검색어로 시작
    else if ([...names, ...extra].some((n) => n.includes(q))) score = 1; // 어딘가에 들어 있음
    if (score >= 0) results.push({ term, score });
  }

  // 점수 높은 순 → 같은 점수면 영어 이름 A-B-C 순 (대소문자 구분 없이: MoSCoW, MVP 순)
  // 데이터 파일에 어떤 순서로 넣든 화면에서는 늘 알파벳 순으로 보인다 → 새 용어도 자동으로 제자리에 들어간다
  results.sort((a, b) => b.score - a.score || compareName(a.term, b.term));
  return results.map((r) => r.term);
}

function compareName(a, b) {
  return a.term_en.localeCompare(b.term_en, "en", { sensitivity: "base", numeric: true });
}

// 목록 머리글자: A, B, C … (숫자나 기호로 시작하면 #)
function initialOf(term) {
  const c = term.term_en.trim().charAt(0).toUpperCase();
  return /[A-Z]/.test(c) ? c : "#";
}

// 카드에서 이전·다음으로 넘길 순서. 목록에서 고른 단계·검색 결과를 그대로 따른다.
// 그 안에 없는 용어(예: "함께 보면 좋은 용어" 링크로 들어옴)면 전체 용어 순서를 쓴다.
function sequenceFor(id) {
  const filtered = searchTerms();
  if (filtered.some((term) => term.id === id)) return filtered;
  const savedQuery = state.query, savedStage = state.stage;
  state.query = ""; state.stage = "all";
  const all = searchTerms();
  state.query = savedQuery; state.stage = savedStage;
  return all;
}

/* ---------- 맨 위 막대 ---------- */
// 목록·정보: 앱 이름을 크게. 카드: 단어가 위로 올라오도록 한 줄로 작게 (← 목록 | 필드워드)
function renderTopbar(kind) {
  if (kind === "home") {
    topbar.className = "topbar";
    topbar.replaceChildren(h("a", { class: "brand", href: "#/" },
      t("app.name") + " ", h("span", { class: "brand-en" }, "Field Words"), h("small", {}, t("app.subtitle"))));
  } else {
    topbar.className = "topbar compact";
    topbar.replaceChildren(
      h("a", { class: "btn small", href: "#/" }, t("nav.back")),
      h("a", { class: "brand-mini", href: "#/" }, t("app.name") + " ", h("span", { class: "brand-mini-en" }, "Field Words"))
    );
  }
}

/* ---------- 화면 1: 목록 ---------- */

function renderList() {
  renderTopbar("home");
  const results = h("div");

  // 검색어나 단계를 바꾸면 결과 부분만 다시 그린다. (검색창을 다시 그리면 입력 중이던 글자 포커스가 사라진다)
  function update() {
    const found = searchTerms();
    results.replaceChildren(
      h("div", { class: "list-head" },
        h("p", { class: "muted" }, t("search.count", { n: found.length })),
        // 지금 보이는 용어들을 첫 카드부터 🚶 이동 중 모드로 연다
        found.length > 0 && h("button", {
          class: "btn primary",
          type: "button",
          onclick: () => { state.mode = "walk"; state.hold = false; location.hash = `#/term/${found[0].id}`; },
        }, icon("walk"), t("walk.entry"))
      ),
      found.length
        ? (state.query ? h("ul", { class: "list" }, found.map(listItem)) : alphabetList(found))
        : h("p", { class: "muted" }, t("search.empty"))
    );
  }

  const input = h("input", {
    class: "search",
    type: "search",
    placeholder: t("search.placeholder"),
    "aria-label": t("search.placeholder"),
    value: state.query,
    oninput: (e) => { state.query = e.target.value; update(); },
  });

  const chips = h("div", { class: "chips", role: "group", "aria-label": t("filter.stage") },
    ["all", ...STAGES].map((stage) =>
      h("button", {
        class: "chip",
        type: "button",
        "aria-pressed": String(state.stage === stage),
        onclick: (e) => {
          state.stage = stage;
          chips.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", "false"));
          e.currentTarget.setAttribute("aria-pressed", "true");
          update();
        },
      }, stage === "all" ? t("filter.all") : t(`stage.${stage}`))
    )
  );

  // 첫 방문 안내는 맨 아래에 둔다: 처음 화면의 주인공은 오늘의 학습과 용어 목록
  app.replaceChildren(todayPanel(), input, chips, results, firstNotice() ?? "");
  update();
}

// 목록 맨 위 "오늘의 학습": 진행 링 + 남은 양 + 시작 버튼 + 상태별 개수
function todayPanel() {
  const p = Review.plan(state.terms, { extra: state.extraGoal });
  const { min_goal } = Review.getSettings();
  const c = Review.counts(state.terms);
  const left = p.queue.length;

  // 목표를 채웠고 더 낼 카드도 없으면(용어를 모두 봄) 버튼 대신 안내만 보여 준다
  const more = left ? left : moreLeft();
  const button = more === 0 ? "" : h("button", {
    class: "btn primary",
    type: "button",
    onclick: () => {
      if (!left) state.extraGoal += 5;                // 목표를 채운 뒤에는 5장 더
      state.session = null;
      location.hash = "#/study";
    },
  }, p.done === 0 ? t("today.start") : left ? t("today.continue") : more >= 5 ? t("today.more") : t("today.more.n", { n: more }));

  const progressLink = h("a", { class: "status-chip progress-link", href: "#/progress" }, t("prog.link"));
  const stats = c.unseen === state.terms.length ? h("div", { class: "status-row" }, progressLink) : h("div", { class: "status-row" },
    ["known", "shaky", "confused", "misconception", "unknown"].map((k) =>
      h("span", { class: `status-chip ${k}` }, `${t(`status.${k}`)} ${c[k]}`)),
    h("span", { class: "status-chip longterm" }, `${t("status.longTerm")} ${c.longTerm}`),
    progressLink
  );

  return h("section", { class: "today" },
    h("div", { class: "today-main" },
      progressRing(p.done, p.goal, 56),
      h("div", { class: "today-text" },
        h("p", { class: "today-title" }, t("today.title", { done: p.done, goal: p.goal }),
          p.done >= min_goal && h("span", { class: "today-min" }, t("today.min.ok"))),
        h("p", { class: "muted" }, left
          ? t("today.left", { n: left, m: p.minutesLeft, r: p.reviewCount, f: p.newCount })
          : more ? t("today.done") : t("done.allseen", { n: state.terms.length }))
      ),
      button
    ),
    stats
  );
}

// 진행 링: 오늘 목표 대비 채운 비율을 원으로 보여 준다
function progressRing(done, goal, size) {
  const ns = "http://www.w3.org/2000/svg";
  const r = size / 2 - 5, len = 2 * Math.PI * r;
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
  svg.setAttribute("class", "pring");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `${done} / ${goal}`);
  const circle = (cls, offset) => {
    const c = document.createElementNS(ns, "circle");
    c.setAttribute("cx", size / 2); c.setAttribute("cy", size / 2); c.setAttribute("r", r);
    c.setAttribute("class", cls);
    if (offset != null) { c.style.strokeDasharray = `${len}`; c.style.strokeDashoffset = `${offset}`; }
    return c;
  };
  const ratio = goal ? Math.min(done / goal, 1) : 0;
  svg.append(circle("ring-track"), circle("ring-bar", len * (1 - ratio)));
  svg.style.width = svg.style.height = `${size}px`;
  return svg;
}

/* ---------- 화면: 오늘의 학습 (체크) ---------- */
// 한 장의 흐름: ① 떠올리기(확신도) → ② 확인 문제 → ③ 결과
// "몰라요"는 확인 문제 없이 바로 카드를 펼쳐 공부한다. 틀리거나 모르면 3장 뒤에 다시 나온다.

const REQUEUE_GAPS = [3, 10];   // 같은 학습 안에서 다시 나오는 간격: 처음 3장 뒤, 또 틀리면 10장 뒤

function renderStudy() {
  renderTopbar("card");
  if (!state.session) {
    const p = Review.plan(state.terms, { extra: state.extraGoal });
    // answers: 몇 번째 카드를 어떤 상태로 체크했는지. 이전 카드로 돌아갔을 때 다시 채점하지 않으려고 기억한다.
    // kinds:   몇 번째 카드가 "learn"(배우기 카드)인지 "check"(체크 카드)인지
    state.session = { queue: p.queue, i: 0, retries: {}, answers: {}, kinds: {} };
  }
  const s = state.session;
  s.kinds ??= {};
  if (s.i >= s.queue.length) {
    // 오늘 할 카드를 다 했으면: 마무리할 것이 있으면 오늘의 마무리 안내, 없으면 마침 화면
    if (!s.wrapOffered) {
      s.wrapOffered = true;
      const ids = Review.planWrap(state.pairs);
      if (ids.length) { state.wrap = { ids, i: 0, step: "intro", right: [], fixed: [], retried: [] }; renderWrap(); return; }
    }
    renderStudyDone();
    return;
  }

  const term = state.allById.get(s.queue[s.i]);
  const goal = Review.getSettings().daily_goal + state.extraGoal;

  // 위쪽 진행 표시: 답할 때마다 다시 그린다
  const head = h("div", { class: "study-head" });
  const paintHead = () => {
    const done = Review.getToday().seen.length;
    // 주의: replaceChildren에 undefined를 넘기면 글자 "undefined"가 찍힌다. 없을 때는 빈 글자("")를 넘긴다.
    head.replaceChildren(
      progressRing(done, goal, 36),
      h("span", {}, t("today.title", { done, goal })),
      // 앞에서 이미 나왔던 용어면 표시: 배우기 카드로만 나왔으면 "방금 배운 용어", 틀려서 다시 나왔으면 "다시 나온 용어"
      againBadge()
    );
  };
  function againBadge() {
    const before = s.queue.slice(0, s.i).map((id, idx) => (id === term.id ? idx : -1)).filter((idx) => idx >= 0);
    if (!before.length) return "";
    const onlyLearned = before.every((idx) => s.kinds[idx] === "learn");
    return h("span", { class: "badge" }, t(onlyLearned ? "study.learned" : "study.again"));
  }
  paintHead();

  const card = h("article", { class: "card" },
    h("div", { class: "term-head", "data-sec": "term" },
      h("h1", {}, term.term_en, h("span", { class: "pron" }, `[${term.pronunciation.ko}]`)),
      speech.supported && speakButton("term", t("speak.term"), () => termOnlyParts(term), "mini")
    )
  );
  const panel = h("div", { class: "check" });
  card.append(panel);

  // 아래 막대: 왼쪽 ⏮ 이전(첫 카드가 아니면) · 가운데 전체 듣기 · 오른쪽 다음 (듣기·다음은 답한 뒤에 나타난다)
  // 넣을 버튼이 하나도 없으면(첫 카드의 답하기 전) 빈 흰 줄이 남지 않게 막대를 숨긴다
  const inner = h("div", { class: "bottom-inner" });
  const bar = h("nav", { class: "bottom-bar", "aria-label": t("controls.label") }, inner);
  const syncBar = () => {
    bar.hidden = inner.childElementCount === 0;
    document.body.classList.toggle("has-bottom-bar", !bar.hidden);
  };
  if (s.i > 0) inner.append(h("button", { class: "ctrl", type: "button", "aria-label": t("check.prev"), onclick: () => { s.i -= 1; route(); } }, icon("prev")));
  app.replaceChildren(head, card, bar);
  syncBar();
  window.scrollTo(0, 0);

  // 이미 체크한 카드로 돌아온 경우: 다시 채점하지 않고(기록이 두 번 남지 않게) 결과와 카드만 보여 준다
  const answered = s.answers[s.i];
  if (answered) {
    panel.replaceChildren(h("p", { class: `result-title ${answered.status}` }, t("check.already", { status: t(`status.${answered.status}`) })));
    showFullCard(true);
    return;
  }

  // 이 자리의 카드 종류를 처음 볼 때 정한다:
  //   처음 보는 용어(기록 없음)이고 이 학습에서 아직 배우지 않았으면 → 배우기 카드
  //   그 밖에는 → 체크 카드 (복습은 문제부터: 먼저 떠올려 보는 것이 가장 오래 남는다)
  s.learned ??= [];
  if (!s.kinds[s.i]) s.kinds[s.i] = !Review.get(term.id) && !s.learned.includes(term.id) ? "learn" : "check";
  if (s.kinds[s.i] === "learn") { showLearn(); return; }

  if (speech.supported) speech.start("term", termOnlyParts(term));

  // ① 떠올리기: 확신도 한 번 누르기
  panel.replaceChildren(
    h("p", { class: "check-prompt" }, t("check.recall")),
    h("div", { class: "conf-row" },
      ["sure", "unsure", "dontknow"].map((c) =>
        h("button", { class: `btn conf ${c}`, type: "button", onclick: () => onConfidence(c) }, t(`check.${c}`)))
    )
  );

  function onConfidence(confidence) {
    if (confidence === "dontknow") return finish({ confidence, correct: false, chosen: null, quiz: null });
    showQuiz(confidence);
  }

  // ② 확인 문제: 4지선다, 한 번 누르면 바로 채점
  function showQuiz(confidence) {
    const quiz = Review.makeQuiz(term, state.terms, state.pairs);
    const question = quiz.kind === "def"
      ? t("check.q.def", { term: term.term_en })
      : t("check.q.term", { def: firstSentence(term.definition) });
    panel.replaceChildren(
      h("p", { class: "check-prompt" }, question),
      h("div", { class: "options" }, quiz.options.map((o) => {
        const x = state.allById.get(o.id);
        const label = quiz.kind === "def" ? firstSentence(x.definition) : `${x.term_en} · ${x.term_ko}`;
        return h("button", { class: "option", type: "button", onclick: () => finish({ confidence, correct: o.correct, chosen: x, quiz }) }, label);
      }))
    );
  }

  // ③ 결과: 기록하고, 결과 화면과 카드 전체를 보여 준다
  function finish({ confidence, correct, chosen, quiz }) {
    const confusedWith = !correct && chosen ? chosen.id : null;
    const { status } = Review.record(term.id, { confidence, correct, quiz: quiz?.kind ?? "recall", confusedWith });
    const bad = status === "misconception" || status === "confused" || status === "unknown";
    s.answers[s.i] = { status };
    paintHead();

    // 틀리거나 모르면 같은 학습 안에서 다시 나오게 한다 (3장 뒤 → 10장 뒤)
    if (bad) {
      const n = s.retries[term.id] ?? 0;
      if (n < REQUEUE_GAPS.length) {
        s.retries[term.id] = n + 1;
        s.queue.splice(Math.min(s.i + 1 + REQUEUE_GAPS[n], s.queue.length), 0, term.id);
      }
    }

    panel.replaceChildren(resultBox(term, status, chosen, quiz));
    showFullCard(bad);
  }

  // 결과 아래에 카드 전체(뜻·예문·함정…)를 붙여 바로 공부할 수 있게 한다. 맞았으면 접어 둔다.
  // 그리고 아래 막대에 "전체 듣기"(가운데)와 "다음"(오른쪽)을 붙인다 — 카드 화면과 같은 자리 약속
  function showFullCard(open) {
    const full = buildCard(term, "");
    full.classList.add("study-full");
    const wrap = open ? full : h("details", { class: "study-more" }, h("summary", {}, t("check.more")), full);
    card.after(wrap);

    // 전체 듣기를 누르면 접혀 있던 카드도 펼치고, 읽는 구역에 색을 칠한다
    speech.onSentence = (part) => highlight(full, part.sec);
    const listen = listenButton(term, () => { if (wrap.tagName === "DETAILS") wrap.open = true; });
    const nextBtn = h("button", { class: "ctrl go", type: "button", onclick: () => { s.i += 1; route(); } },
      h("span", {}, s.i + 1 < s.queue.length ? t("check.next") : t("check.finish")), icon("next"));
    inner.append(listen, nextBtn);
    syncBar();
  }

  // 처음 보는 용어: 먼저 배우기 카드
  //   카드 전체를 보여 주고(전체 듣기 가능) → [익혔어요]를 누르면 다른 카드 3장 뒤에 확인 문제로 다시 나온다.
  //   바로 묻지 않는 이유: 방금 본 것을 바로 물으면 기억이 아니라 눈앞의 잔상으로 맞힌다 (간격 효과)
  //   [이미 알아요]: 배우기를 건너뛰고 바로 확인 문제로. 틀리면 착각으로 잡히므로 놓치지 않는다.
  function showLearn() {
    panel.replaceChildren(h("div", { class: "learn-box" },
      h("p", { class: "learn-title" }, t("learn.title")),
      h("p", { class: "learn-body" }, t("learn.body", { n: LEARN_GAP })),
      h("button", { class: "btn small", type: "button", onclick: alreadyKnow }, t("learn.know"))
    ));
    const full = buildCard(term, "");
    full.classList.add("study-full");
    card.after(full);
    speech.onSentence = (part) => highlight(full, part.sec);
    const doneBtn = h("button", { class: "ctrl go", type: "button", onclick: learned }, h("span", {}, t("learn.done")), icon("next"));
    inner.append(listenButton(term), doneBtn);
    syncBar();
    if (speech.supported) speech.start("term", termOnlyParts(term));
  }

  function learned() {
    // 이전 버튼으로 돌아와 다시 누른 경우에는 확인 문제를 또 넣지 않는다
    if (!s.learned.includes(term.id)) {
      s.learned.push(term.id);
      s.queue.splice(Math.min(s.i + 1 + LEARN_GAP, s.queue.length), 0, term.id);
    }
    s.i += 1;
    route();
  }

  function alreadyKnow() {
    if (!s.learned.includes(term.id)) s.learned.push(term.id);
    s.kinds[s.i] = "check";
    route();
  }
}

const LEARN_GAP = 3;   // 배운 용어를 확인 문제로 다시 낼 때까지 사이에 둘 카드 수

// 아래 막대의 "전체 듣기" 큰 버튼 (재생 ↔ 일시정지 ↔ 이어 듣기). beforePlay: 재생 전에 할 일
function listenButton(term, beforePlay) {
  const btn = h("button", { class: "ctrl main", type: "button", onclick: () => { beforePlay?.(); speech.toggle("all", () => fullParts(term)); } });
  const paint = () => {
    const mine = speech.owner === "all";
    const playing = mine && speech.status === "playing";
    const paused = mine && speech.status === "paused";
    btn.classList.toggle("playing", playing);
    btn.setAttribute("aria-pressed", String(playing));
    btn.replaceChildren(
      icon(playing ? "pause" : paused ? "play" : "speaker"),
      h("span", {}, playing ? t("speak.pause") : paused ? t("speak.resume") : t("speak.all"))
    );
  };
  speech.listeners.add(paint);
  speech.listeners.add(() => { if (speech.status === "idle") document.querySelectorAll(".reading").forEach((e) => e.classList.remove("reading")); });
  paint();
  return btn;
}

function firstSentence(text) {
  const m = text.match(/^.*?[.?!](?=\s|$)/);
  return m ? m[0] : text;
}

// 결과 상자. 틀렸을 때는 빨간 ✗ 대신 내 답과 정답을 나란히 보여 준다 (콘텐츠 작성 가이드 8장)
function resultBox(term, status, chosen, quiz) {
  const title = h("p", { class: `result-title ${status}` }, t(`result.${status}`));
  const parts = [title];

  if (chosen && chosen.id !== term.id) {
    const pair = state.pairs.find((p) => [p.a, p.b].includes(term.id) && [p.a, p.b].includes(chosen.id));
    const side = (id) => (pair ? (pair.a === id ? "a" : "b") : null);
    const show = (x, label, cls) => h("div", { class: `cmp-box ${cls} ${side(x.id) ? `pair-${side(x.id)}` : ""}` },
      h("span", { class: "cmp-label" }, label),
      h("b", {}, `${x.term_en} · ${x.term_ko}`),
      h("span", {}, firstSentence(x.definition)));
    parts.push(h("div", { class: "cmp" }, show(chosen, t("result.mine"), "mine"), show(term, t("result.answer"), "answer")));
    if (pair) parts.push(h("p", { class: "pair-diff" }, h("b", {}, t("card.pair.diff")), pair.difference));
  } else {
    parts.push(h("p", {}, firstSentence(term.definition)));
  }
  // 현업 함정은 결과 바로 아래에 펼쳐지는 카드 전체에 있으므로 여기서는 반복하지 않는다
  if (status === "misconception" || status === "confused" || status === "unknown") parts.push(h("p", { class: "muted" }, t("result.again")));
  return h("div", { class: "result" }, parts);
}

// 오늘 할 카드를 다 했을 때: 구체적인 칭찬 + 상태별 개수 (오늘의 마무리 전체 버전은 다음 작업)
// 칭찬 단계: 목표를 넘어 5장 더 할 때마다 한 단계씩 커진다
//   0: 목표 전에 끝남(용어가 모자랄 때)  1: 목표 달성 🎉  2: +5장 🔥  3: +10장 🚀  4: +15장 이상 🏆
// 4단계에서는 "내일은 쉬엄쉬엄"을 함께 말한다. 몰아서 하는 것보다 매일 조금씩이 오래 남기 때문이다.
function praiseTier(done, goal) {
  if (done < goal) return 0;
  return Math.min(1 + Math.floor((done - goal) / 5), 4);
}

function renderStudyDone() {
  const today = Review.getToday();
  const goal = Review.getSettings().daily_goal;
  const done = today.seen.length;
  const tier = praiseTier(done, goal);

  // 용어 이름표: 누르면 그 용어 카드로 간다
  const chips = (ids, cls) => h("div", { class: "done-chips" },
    ids.map((id) => state.allById.get(id)).filter(Boolean).map((x) =>
      h("a", { class: `done-chip ${cls}`, href: `#/term/${x.id}` }, x.term_en)));

  const corrected = today.corrected;
  const found = today.misconceptions;

  // 축하 종이 조각은 새 단계에 처음 올라섰을 때만 뿌린다 (같은 화면을 다시 열 때마다 나오지 않게)
  const celebrate = tier > 0 && tier > state.celebratedTier;
  if (celebrate) state.celebratedTier = tier;

  app.replaceChildren(
    celebrate ? confetti(tier) : "",
    h("article", { class: `card done tier-${tier}` },
      h("div", { class: "done-hero" },
        progressRing(done, Math.max(goal, done), 72),
        h("div", {},
          h("h1", {}, t(`done.tier${tier}.title`)),
          h("p", { class: "done-sub" }, t(`done.tier${tier}.sub`, { n: done, extra: Math.max(done - goal, 0) }))
        )
      ),

      // 🌙 마무리 결과: 구체적으로 칭찬한다 (몇 개를 다시 떠올렸는지, 어떤 것을 바로잡았는지)
      state.wrapResult && h("section", { class: "done-box wrapbox" },
        h("p", { class: "done-box-title" }, t("wrap.result", { r: state.wrapResult.right, n: state.wrapResult.total })),
        state.wrapResult.fixed.length > 0 && h("p", { class: "done-box-body" },
          t("wrap.fixed", { names: state.wrapResult.fixed.map((id) => state.allById.get(id)?.term_en).join(", ") }))
      ),

      // ✨ 바로잡은 용어: 틀렸다가 다시 맞힌 것. 실력이 느는 순간이라 가장 크게 칭찬한다
      corrected.length > 0 && h("section", { class: "done-box gold" },
        h("p", { class: "done-box-title" }, t("done.corrected.title", { k: corrected.length })),
        chips(corrected, "gold"),
        h("p", { class: "done-box-body" }, t("done.corrected.body"))
      ),

      // 🔍 찾아낸 착각: 확실했는데 달랐던 것. 찾아낸 것 자체가 수확이라고 말해 준다
      found.length > 0 && h("section", { class: "done-box warm" },
        h("p", { class: "done-box-title" }, t("done.found.title", { k: found.length })),
        chips(found, "warm"),
        h("p", { class: "done-box-body" }, t("done.found.body"))
      ),

      h("div", { class: "done-actions" },
        h("a", { class: "btn", href: "#/" }, t("nav.back")),
        h("a", { class: "btn", href: "#/progress" }, t("prog.link")),
        moreAction(today)
      ),
      moreLeft(today) === 0 && h("p", { class: "muted done-note" }, t("done.allseen", { n: state.terms.length }))
    )
  );
  state.session = null;
  state.wrapResult = null;
}

/* ---------- 화면: 오늘의 마무리 (Must #15) ---------- */
// 2~3분 동안 오늘 카드를 다시 떠올린다. 한 칸 쉬운 문제(용어 → 뜻 고르기)로, 확신도는 묻지 않는다.
// 틀린 카드는 마무리 끝에서 한 번 더 나온다. 답은 복습 날짜를 바꾸지 않는다 (Review.practice).
function renderWrap() {
  renderTopbar("card");
  speech.stop();
  const w = state.wrap;
  const total = w.ids.length;

  if (w.step === "intro") {
    app.replaceChildren(h("article", { class: "card wrap" },
      h("h1", {}, t("wrap.title")),
      h("p", {}, t("wrap.intro", { n: total, m: Math.max(1, Math.round((total * 20) / 60)) })),
      h("p", { class: "muted" }, t("wrap.note")),
      h("div", { class: "done-actions" },
        h("button", { class: "btn", type: "button", onclick: endWrap }, t("wrap.skip")),
        h("button", { class: "btn primary", type: "button", onclick: () => { w.step = "q"; renderWrap(); } }, t("wrap.start")))
    ));
    return;
  }
  if (w.i >= w.ids.length) { endWrap(); return; }

  const term = state.allById.get(w.ids[w.i]);
  const quiz = Review.makeQuiz(term, state.terms, state.pairs, Math.random, "def");
  const panel = h("div", { class: "check" });
  app.replaceChildren(
    h("div", { class: "study-head" }, h("span", { class: "badge" }, t("wrap.badge")), h("span", {}, t("wrap.progress", { i: w.i + 1, n: w.ids.length }))),
    h("article", { class: "card" },
      h("div", { class: "term-head" }, h("h1", {}, term.term_en, h("span", { class: "pron" }, `[${term.pronunciation.ko}]`))),
      panel)
  );
  window.scrollTo(0, 0);
  panel.replaceChildren(
    h("p", { class: "check-prompt" }, t("check.q.def", { term: term.term_en })),
    h("div", { class: "options" }, quiz.options.map((o) => {
      const x = state.allById.get(o.id);
      return h("button", { class: "option", type: "button", onclick: () => answer(o.correct, x) }, firstSentence(x.definition));
    }))
  );

  function answer(correct, chosen) {
    const wasWrong = Review.getToday().wrong.includes(term.id);
    Review.practice(term.id, correct);
    if (correct) {
      // "바로 떠올린 것"은 첫 번째에 맞힌 것만 센다 (다시 나와서 맞힌 것은 "바로잡은 것"으로 따로 칭찬)
      if (!w.retried.includes(term.id) && !w.right.includes(term.id)) w.right.push(term.id);
      if (wasWrong && !w.fixed.includes(term.id)) w.fixed.push(term.id);
    } else if (!w.retried.includes(term.id)) {
      // 틀리면 마무리 끝에서 한 번 더. 단, 마지막 "맞힐 카드"보다는 앞에 둔다
      w.retried.push(term.id);
      w.ids.splice(Math.max(w.ids.length - 1, w.i + 1), 0, term.id);
    }
    panel.replaceChildren(resultBox(term, correct ? "known" : "confused", correct ? null : chosen, quiz));
    if (!correct && term.pitfall) panel.append(h("p", { class: "muted" }, h("b", {}, t("card.pitfall")), " ", term.pitfall));
    panel.append(h("div", { class: "done-actions" },
      h("button", { class: "btn primary", type: "button", onclick: () => { w.i += 1; renderWrap(); } },
        w.i + 1 < w.ids.length ? t("check.next") : t("wrap.finish"))));
  }
}

function endWrap() {
  const w = state.wrap;
  Review.markWrapped(w.ids);
  state.wrapResult = w.step === "intro" ? null : { total: new Set(w.ids).size, right: w.right.length, fixed: w.fixed };
  state.wrap = null;
  renderStudyDone();
}

// 오늘 더 낼 수 있는 새·복습 카드 수 (5장 더 하기를 눌렀을 때 실제로 나올 장 수)
function moreLeft() {
  return Review.plan(state.terms, { extra: state.extraGoal + 5 }).queue.length;
}

// 마침 화면의 두 번째 버튼
//   더 낼 카드가 있으면: "5장 더 하기" (남은 게 5장보다 적으면 그 수만큼)
//   모두 봤으면: 오늘 틀렸던 용어를 한 번 더 풀기 (틀린 게 없으면 버튼 없음)
function moreAction(today) {
  const left = moreLeft();
  if (left > 0) {
    return h("button", { class: "btn primary", type: "button", onclick: () => { state.extraGoal += 5; state.session = null; route(); } },
      left >= 5 ? t("today.more") : t("today.more.n", { n: left }));
  }
  const again = [...new Set(today.wrong)];
  if (!again.length) return "";
  return h("button", {
    class: "btn primary",
    type: "button",
    onclick: () => {
      state.session = { queue: again, i: 0, retries: {}, answers: {} };
      route();
    },
  }, t("done.retry", { n: again.length }));
}

// 축하 종이 조각: 칭찬 단계가 높을수록 조각이 많아진다. 한 번만 떨어지고 사라진다.
// 화면 움직임을 줄이도록 설정한 사람(prefers-reduced-motion)에게는 CSS에서 보이지 않게 한다.
function confetti(tier) {
  const colors = ["var(--accent)", "var(--pair-b)", "var(--pair-a-border)", "var(--gold)", "var(--warm)"];
  const count = [0, 18, 28, 40, 56][tier];
  const box = h("div", { class: "confetti", "aria-hidden": "true" });
  for (let i = 0; i < count; i++) {
    const piece = h("span", {});
    piece.style.left = `${Math.random() * 100}%`;
    piece.style.background = colors[i % colors.length];
    piece.style.animationDelay = `${Math.random() * 0.6}s`;
    piece.style.transform = `rotate(${Math.random() * 360}deg)`;
    box.append(piece);
  }
  setTimeout(() => box.remove(), 3000);
  return box;
}

// 데이터 한계 안내는 처음 한 번만 짧게 보여 준다. "확인"을 누르면 다시 나오지 않는다.
// 자세한 내용은 맨 아래 "정보" 링크에서 필요한 사람만 본다.
const NOTICE_KEY = "fw:v1:notice_seen";
function firstNotice() {
  try { if (localStorage.getItem(NOTICE_KEY)) return null; } catch { /* 저장소를 못 쓰는 환경이면 그냥 보여 준다 */ }
  const box = h("div", { class: "first-notice", role: "note" },
    h("p", {}, t("notice.short")),
    h("a", { class: "btn", href: "#/about" }, t("notice.more")),
    h("button", {
      class: "btn primary",
      type: "button",
      onclick: () => {
        try { localStorage.setItem(NOTICE_KEY, "1"); } catch { /* 무시 */ }
        box.remove();
      },
    }, t("notice.ok"))
  );
  return box;
}

// 검색어가 없을 때: 알파벳 머리글자(A, B, C …)로 묶어서 보여 준다. 사전처럼 찾기 쉽게.
// (검색 중에는 가장 잘 맞는 용어가 맨 위에 와야 해서 묶지 않는다)
function alphabetList(terms) {
  const groups = new Map();
  for (const term of terms) {
    const k = initialOf(term);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(term);
  }
  return h("div", {}, [...groups].map(([letter, list]) =>
    h("section", { class: "alpha-group" },
      h("h2", { class: "alpha-head" }, letter),
      h("ul", { class: "list" }, list.map(listItem))
    )));
}

function listItem(term) {
  return h("li", {},
    h("a", { href: `#/term/${term.id}` },
      h("span", { class: "term-en" }, term.term_en),
      h("span", { class: "term-ko" }, term.term_ko),
      h("span", { class: "term-def" }, term.definition)
    )
  );
}

/* ---------- 화면 2: 용어 카드 (모드 3개가 같은 화면을 쓴다) ---------- */

function renderTerm(id) {
  const term = state.allById.get(id);
  // 이름이 바뀐 용어의 옛 주소로 들어오면 새 용어로 보낸다
  if (term?.replaced_by) { location.replace(`#/term/${term.replaced_by}`); return; }
  renderTopbar("card");
  if (!term) { app.replaceChildren(h("p", {}, t("card.not_found"))); return; }

  const seq = sequenceFor(term.id);
  const index = seq.findIndex((x) => x.id === term.id);
  const goTo = (i) => { if (i >= 0 && i < seq.length) location.hash = `#/term/${seq[i].id}`; };

  const card = buildCard(term, seq.length > 1 ? `${index + 1} / ${seq.length}` : "");
  const controls = buildControls(term, index, seq.length, goTo);

  // 🗣️ 말하기: 답(뜻·예문 등)을 가리고, 30초 동안 먼저 설명해 보게 한다
  const practice = state.mode === "speak" ? speakPractice(card, term, index < seq.length - 1, () => goTo(index + 1)) : null;

  app.replaceChildren(modeBar(term, controls), card, controls.bar);
  if (practice) (card.querySelector(".term-ko-big") ?? card.querySelector(".term-head")).after(practice);
  document.body.classList.add("has-bottom-bar");
  window.scrollTo(0, 0);

  // 지금 읽는 문장의 구역에 색을 칠하고, 그 구역이 화면 가운데 오도록 내린다 (귀와 눈으로 같은 내용을 받게)
  speech.onSentence = (part) => highlight(card, part.sec);
  speech.listeners.add(() => { if (speech.status === "idle") highlight(card, null); });
  updateMediaSession(term, controls.toggle, () => goTo(index + 1), () => goTo(index - 1));

  // 모드에 따라 카드를 열자마자 할 일
  const hold = state.hold;
  state.hold = false;
  if (state.mode === "speak") {
    // 용어를 들려준 뒤 30초 타이머를 시작한다 (소리를 못 내는 기기면 바로 시작)
    if (!hold && speech.supported) speech.start("term", termOnlyParts(term), () => practice.startTimer());
    else practice.startTimer();
    return;
  }
  if (hold || !speech.supported) return;
  if (state.mode === "walk") controls.playFull();
}

// 🗣️ 말하기 연습 상자
//   1) 답을 가린 채 원형 타이머가 30초 동안 줄어든다 → 그동안 소리 내어 설명해 본다
//   2) 시간이 다 되면(또는 "답 보기"를 누르면) 답을 펼치고 뜻을 읽어 준다
//   3) 다음 용어까지 5초 세고 자동으로 넘어간다. "지금 넘기기"로 빨리, "여기 머물기"로 멈출 수 있다
// 먼저 떠올려 말해 보고 나서 답을 보면 기억에 더 오래 남는다 (인출 연습).
const SPEAK_SECONDS = 30;
const SPEAK_NEXT_SECONDS = 5;
const RING_R = 26;
const RING_LEN = 2 * Math.PI * RING_R;

function speakPractice(card, term, hasNext, goNext) {
  card.classList.add("concealed");

  // 원형 타이머: 글자 대신 원이 줄어드는 모양으로 남은 시간을 보여 준다 (흘끗 봐도 알 수 있게)
  const ns = "http://www.w3.org/2000/svg";
  const ring = document.createElementNS(ns, "svg");
  ring.setAttribute("viewBox", "0 0 64 64");
  ring.setAttribute("class", "ring");
  ring.setAttribute("aria-hidden", "true");
  const track = document.createElementNS(ns, "circle");
  const bar = document.createElementNS(ns, "circle");
  for (const c of [track, bar]) { c.setAttribute("cx", "32"); c.setAttribute("cy", "32"); c.setAttribute("r", String(RING_R)); }
  track.setAttribute("class", "ring-track");
  bar.setAttribute("class", "ring-bar");
  bar.style.strokeDasharray = `${RING_LEN}`;
  bar.style.strokeDashoffset = "0";
  ring.append(track, bar);
  const seconds = h("span", { class: "ring-num" }, `${SPEAK_SECONDS}`);
  const timer = h("div", { class: "ring-wrap", role: "timer", "aria-label": t("speak.timer.label") }, ring, seconds);

  const box = h("div", { class: "speak-box" },
    h("p", { class: "speak-prompt" }, t("speak.prompt", { n: SPEAK_SECONDS })),
    h("div", { class: "speak-row2" },
      timer,
      h("button", { class: "btn primary", type: "button", onclick: () => reveal() }, t("speak.reveal"))
    )
  );

  box.startTimer = () => {
    clearInterval(state.speakTimer);
    let left = SPEAK_SECONDS;
    state.speakTimer = setInterval(() => {
      left -= 1;
      seconds.textContent = `${Math.max(left, 0)}`;
      bar.style.strokeDashoffset = `${RING_LEN * (1 - left / SPEAK_SECONDS)}`;
      if (left <= 0) reveal();            // 시간이 다 되면 바로 답을 펼친다 ("시간 끝" 글자 대신)
    }, 1000);
  };

  // read=false: 아래 "전체 듣기"로 펼칠 때. 그때는 전체 듣기가 읽으므로 여기서는 읽지 않고, 자동 넘김도 하지 않는다.
  function reveal({ read = true } = {}) {
    clearInterval(state.speakTimer);
    card.classList.remove("concealed");
    if (!read) { box.remove(); return; }
    box.replaceWith(nextBox);
    if (speech.supported) {
      speech.start("answer", [{ text: `${t("speak.def_prefix")} ${term.definition}`, lang: "ko-KR", sec: "def" }], startCountdown);
    } else {
      startCountdown();
    }
  }
  box.reveal = reveal;

  // 스스로 채점: 맞음 / 일부 / 아직 → 오늘의 학습과 같은 기록에 남긴다 (한 번 누르기)
  //   맞음 = 확실하게 맞힘(✅ 앎), 일부 = 헷갈렸지만 맞힘(🟡 불안한 앎), 아직 = 모름(⚪)
  const GRADES = { right: { confidence: "sure", correct: true }, partly: { confidence: "unsure", correct: true }, notyet: { confidence: "dontknow", correct: false } };
  const graded = h("p", { class: "muted" });
  const gradeRow = h("div", { class: "grade-row" },
    h("span", { class: "grade-q" }, t("grade.q")),
    Object.keys(GRADES).map((g) => h("button", {
      class: `btn grade ${g}`,
      type: "button",
      onclick: () => {
        Review.record(term.id, { ...GRADES[g], quiz: "speak" });
        stopCountdown();
        if (hasNext) goNext();
        else { gradeRow.remove(); graded.textContent = t("grade.saved"); }
      },
    }, t(`grade.${g}`)))
  );

  // 다음 용어로 넘어가기 전 안내 상자
  const countText = h("span", {});
  const nextBox = h("div", { class: "next-box" },
    gradeRow,
    graded,
    hasNext ? countText : h("span", {}, t("speak.last")),
    hasNext && h("div", { class: "next-actions" },
      h("button", { class: "btn", type: "button", onclick: stay }, t("speak.stay")),
      h("button", { class: "btn primary", type: "button", onclick: () => { stopCountdown(); goNext(); } }, t("speak.next.now"))
    )
  );

  function startCountdown() {
    if (!hasNext) return;
    let left = SPEAK_NEXT_SECONDS;
    countText.textContent = t("speak.next.in", { n: left });
    state.speakTimer = setInterval(() => {
      left -= 1;
      countText.textContent = t("speak.next.in", { n: Math.max(left, 0) });
    }, 1000);
    state.nextTimer = setTimeout(() => { stopCountdown(); goNext(); }, SPEAK_NEXT_SECONDS * 1000);
  }
  function stopCountdown() {
    clearInterval(state.speakTimer);
    clearTimeout(state.nextTimer);
    state.nextTimer = null;
  }
  function stay() {
    stopCountdown();
    nextBox.remove();
  }

  return box;
}

// 모드 전환 막대: 늘 카드 위에 보인다. 한 줄 설명으로 무엇이 일어나는지 알려 준다.
// 🚶 이동 중이 켜진 상태에서 그 버튼을 한 번 더 누르면 일시정지 ↔ 다시 듣기 (아래 큰 버튼과 같은 동작)
function modeBar(term, controls) {
  const desc = h("p", { class: "mode-desc" });
  const buttons = MODES.map((mode) => h("button", {
    class: "mode-btn",
    type: "button",
    "aria-pressed": String(state.mode === mode),
    onclick: () => (mode === state.mode ? pressAgain(mode) : switchMode(mode)),
  }));

  function paint() {
    buttons.forEach((b, i) => {
      const mode = MODES[i];
      const active = mode === state.mode;
      b.setAttribute("aria-pressed", String(active));
      // 이동 중 버튼에는 지금 상태를 작은 아이콘으로 붙인다: 듣는 중이면 ⏸(누르면 멈춤), 멈춰 있으면 ▶(누르면 다시 듣기)
      const extra = active && mode === "walk" && speech.supported ? icon(controls.isPlaying() ? "pause" : "play") : null;
      b.replaceChildren(t(`mode.${mode}`), extra ?? "");
    });
    desc.textContent = t(`mode.${state.mode}.desc`);
  }

  function pressAgain(mode) {
    if (mode === "walk" && speech.supported) controls.toggle();
  }

  function switchMode(mode) {
    // 말하기는 답을 가리는 화면이라, 말하기로 들어가거나 나올 때는 카드를 새로 그린다
    if (mode === "speak" || state.mode === "speak") {
      state.mode = mode;
      route();
      return;
    }
    state.mode = mode;
    if (mode !== "walk" && state.nextTimer) { clearTimeout(state.nextTimer); state.nextTimer = null; }
    // 이동 중으로 바꾸면 지금 카드를 바로 읽기 시작한다 (이미 읽고 있으면 그대로 이어 간다)
    if (mode === "walk" && speech.supported && speech.status !== "playing") {
      if (speech.owner === "all" && speech.status === "paused") speech.run(speech.index);
      else controls.playFull();
    }
    paint();
    syncWakeLock();
  }

  speech.listeners.add(paint);
  paint();
  return h("div", { class: "modebar" },
    h("div", { class: "mode-group", role: "group", "aria-label": t("mode.label") }, buttons),
    desc
  );
}

// 카드 본문. 읽기 구역마다 data-sec 이름을 붙여, 읽는 중인 곳에 색을 칠할 수 있게 한다.
function buildCard(term, progressText) {
  const pron = term.pronunciation;
  return h("article", { class: "card" },
    // 카드 머리: 단어(왼쪽) + 진행·단계·등급(오른쪽 위). 화면이 좁아 한 줄에 안 들어가면 진행 표시가 단어 위로 올라간다.
    h("div", { class: "card-head" },
      h("div", { class: "term-head", "data-sec": "term" },
        h("h1", {}, term.term_en, h("span", { class: "pron" }, `[${pron.ko}]`)),
        speech.supported && speakButton("term", t("speak.term"), () => termOnlyParts(term), "mini")
      ),
      h("span", { class: "card-progress" }, progressText, progressText && " · ", t(`stage.${term.stage}`), " · ", t(`level.${term.level}`))
    ),
    term.term_ko !== term.term_en && h("p", { class: "term-ko-big" }, term.term_ko),
    (pron.note || pron.variants?.length > 0) && h("p", { class: "pron-tip" },
      pron.note && h("span", {}, pron.note),
      pron.variants?.length > 0 && h("span", {}, `${t("card.variants")}: ${pron.variants.join(", ")}`)
    ),
    term.expansion && h("div", { class: "expansion", "data-sec": "expansion" },
      h("b", {}, term.expansion),
      term.expansion_ko
    ),
    (term.tags ?? []).length > 0 && h("div", { class: "badges" },
      term.tags.map((tag) => h("span", { class: "badge" }, `#${tag}`))
    ),

    section("def", t("card.definition"), h("p", {}, term.definition)),
    term.analogy && section("analogy", t("card.analogy"), h("p", {}, term.analogy)),
    section(null, t("card.examples"), h("ul", { class: "examples" },
      term.examples.map((ex, i) => h("li", { "data-sec": `ex-${i}` }, h("span", { class: "ctx" }, t(`context.${ex.context}`)), ex.sentence))
    )),
    term.pitfall && section("pitfall", t("card.pitfall"), h("p", { class: "pitfall" }, term.pitfall)),
    pairSection(term),
    term.interview_q && section(null, t("card.interview"),
      h("p", { "data-sec": "interview" }, term.interview_q),
      term.interview_a && interviewPractice(term)
    ),
    linkSection(null, t("card.prerequisites"), term.prerequisites),
    linkSection("related", t("card.related"), term.related),
    term.also_stages?.length > 0 && section(null, t("card.also_stages"),
      h("div", { class: "badges" }, term.also_stages.map((s) => h("span", { class: "badge" }, t(`stage.${s}`))))
    ),
    sourceSection(term),
    h("p", { class: "card-feedback" }, h("a", { href: `#/feedback/${term.id}` }, t("card.feedback")))
  );
}

// 면접 질문 아래: [⏱ 30초 답해 보기] + [모범 답변 보기]
// 30초 답해 보기를 누르면 원형 타이머가 줄어들고, 시간이 다 되면 모범 답변이 저절로 펼쳐진다.
// 바로 보고 싶으면 "모범 답변 보기"를 누르면 된다 (그때는 타이머를 멈춘다).
const INTERVIEW_SECONDS = 30;
function interviewPractice(term) {
  const answer = h("details", { class: "answer", "data-sec": "answer" },
    h("summary", {}, t("card.interview.show")),
    h("p", {}, term.interview_a)
  );
  const ring = countdownRing(INTERVIEW_SECONDS, 44);
  let timer = null;
  const stop = () => { clearInterval(timer); timer = null; };
  answer.addEventListener("toggle", () => { if (answer.open) { stop(); ring.el.remove(); start.hidden = false; } });

  const start = h("button", {
    class: "btn small practice-btn",
    type: "button",
    onclick: () => {
      // 전체 듣기가 읽는 중이면 멈춘다. 그대로 두면 읽기가 "모범 답변"에 닿을 때 답을 펼쳐 버린다.
      // (멈춘 곳은 기억하므로 아래 "이어 듣기"로 계속 들을 수 있다)
      if (speech.status === "playing") speech.pause();
      document.querySelectorAll(".reading").forEach((e) => e.classList.remove("reading"));
      answer.open = false;
      start.hidden = true;
      start.after(ring.el);
      let left = INTERVIEW_SECONDS;
      ring.set(left);
      stop();
      timer = setInterval(() => {
        left -= 1;
        ring.set(left);
        if (!document.body.contains(ring.el)) return stop();     // 화면을 옮겼으면 멈춘다
        if (left <= 0) { stop(); answer.open = true; answer.scrollIntoView({ block: "center", behavior: "smooth" }); }
      }, 1000);
    },
  }, t("card.interview.practice", { n: INTERVIEW_SECONDS }));

  return h("div", { class: "interview-tools" }, h("div", { class: "practice-row" }, start), answer);
}

// 원형 타이머 (원이 시계 방향으로 줄어들고 가운데에 남은 초)
function countdownRing(total, size) {
  const ns = "http://www.w3.org/2000/svg";
  const r = size / 2 - 4, len = 2 * Math.PI * r;
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
  svg.setAttribute("class", "ring");
  svg.style.width = svg.style.height = `${size}px`;
  const mk = (cls) => {
    const c = document.createElementNS(ns, "circle");
    c.setAttribute("cx", size / 2); c.setAttribute("cy", size / 2); c.setAttribute("r", r);
    c.setAttribute("class", cls);
    return c;
  };
  const bar = mk("ring-bar");
  bar.style.strokeDasharray = `${len}`;
  svg.append(mk("ring-track"), bar);
  const num = h("span", { class: "ring-num small" });
  const el = h("div", { class: "ring-wrap", role: "timer", style: `width:${size}px;height:${size}px` }, svg, num);
  const set = (left) => {
    num.textContent = `${Math.max(left, 0)}`;
    bar.style.strokeDashoffset = `${len * (1 - Math.max(left, 0) / total)}`;
  };
  set(total);
  return { el, set };
}

function section(sec, title, ...body) {
  return h("section", { class: "section", "data-sec": sec ?? undefined }, h("h2", {}, title), ...body);
}

function highlight(card, sec) {
  card.querySelectorAll(".reading").forEach((el) => el.classList.remove("reading"));
  if (!sec) return;
  const el = card.querySelector(`[data-sec="${sec}"]`);
  if (!el) return;
  el.classList.add("reading");
  if (el.tagName === "DETAILS") el.open = true;  // 모범 답변을 읽을 때는 펼쳐서 보여 준다
  el.scrollIntoView({ block: "center", behavior: "smooth" });
}

// 혼동 쌍은 confusable_pairs 한곳에만 있다. 이 용어가 들어 있는 쌍을 여기서 찾는다 (단일 진실 공급원).
function pairSection(term) {
  const pairs = state.pairs.filter((p) => p.a === term.id || p.b === term.id);
  if (!pairs.length) return null;
  return section("pair", t("card.pair"), pairs.map((p) => {
    const box = (side) => {
      const other = state.allById.get(p[side]);
      // 지금 보는 용어는 누를 필요가 없으니 링크가 아닌 상자로, "지금 보는 용어" 글자를 붙인다
      if (other.id === term.id) {
        return h("div", { class: `pair-box ${side} current` },
          h("b", {}, other.term_en), other.term_ko, h("br"), h("span", { class: "here" }, t("card.pair.here")));
      }
      return h("a", { class: `pair-box ${side}`, href: `#/term/${other.id}` },
        h("b", {}, other.term_en), other.term_ko);
    };
    return h("div", {},
      h("div", { class: "pair" }, box("a"), box("b")),
      h("p", { class: "pair-diff" }, h("b", {}, t("card.pair.diff")), p.difference)
    );
  }));
}

// 출처는 관리용 기록(sources)이다. 학습자에게 의미 있는 것만 보여 준다:
// 강의 회차("FDE 3회차"), 유튜브·뉴스(링크). 내부 기록(기획 대화, Claude 제안)은 숨긴다.
const PUBLIC_SOURCE_TYPES = ["lecture", "youtube", "news"];
function sourceSection(term) {
  const shown = term.sources.filter((s) => PUBLIC_SOURCE_TYPES.includes(s.type));
  if (!shown.length) return null;
  return section(null, t("card.sources"), h("div", { class: "links" }, shown.map((s) =>
    s.url ? h("a", { href: s.url, target: "_blank", rel: "noopener" }, s.label) : h("span", {}, s.label)
  )));
}

// 다른 용어로 가는 링크. 아직 없는 용어는 점선 이름표로만 보여 준다.
function linkSection(sec, title, ids) {
  if (!ids?.length) return null;
  return section(sec, title, h("div", { class: "links" }, ids.map((id) => {
    const other = state.allById.get(id);
    return other ? h("a", { href: `#/term/${id}` }, other.term_en) : h("span", {}, id);
  })));
}

/* ---------- 아래 고정 막대: ⏮ 이전 · 재생/일시정지 · ⏭ 다음 ---------- */

function buildControls(term, index, total, goTo) {
  const hasPrev = index > 0, hasNext = index < total - 1;

  // 전체 듣기. 이동 중 모드면 다 읽은 뒤 2초 쉬고 다음 카드로 넘어간다.
  const playFull = () => {
    // 말하기 모드: 가린 답을 펼치고(여기서 전부 읽으므로 따로 읽지 않음), 다음 용어 자동 넘김은 멈춘다
    document.querySelector(".speak-box")?.reveal?.({ read: false });
    document.querySelector(".next-box")?.remove();
    clearInterval(state.speakTimer);
    clearTimeout(state.nextTimer);
    state.nextTimer = null;
    speech.start("all", fullParts(term), () => {
      if (state.mode !== "walk" || !hasNext) { syncWakeLock(); return; }
      state.nextTimer = setTimeout(() => { state.nextTimer = null; goTo(index + 1); }, NEXT_CARD_DELAY_MS);
      speech.listeners.forEach((fn) => fn());   // 아래 큰 버튼과 위 모드 버튼 모두 "듣는 중"으로 다시 그린다
    });
  };

  // "듣는 중": 전체 듣기를 읽는 중이거나, 이동 중 모드에서 다음 카드로 넘어가기 전 2초 동안
  const walkGap = () => state.mode === "walk" && state.nextTimer !== null;
  const isPlaying = () => (speech.owner === "all" && speech.status === "playing") || walkGap();

  const toggle = () => {
    if (walkGap()) {                          // 다음 카드로 넘어가기 전 2초 동안 누르면: 다음 카드에서 멈춰 둔다
      clearTimeout(state.nextTimer);
      state.nextTimer = null;
      state.hold = true;
      goTo(index + 1);
      return;
    }
    if (speech.owner === "all" && speech.status === "playing") return speech.pause();
    if (speech.owner === "all" && speech.status === "paused") return speech.run(speech.index);
    playFull();
  };

  // 이전·다음: 이동 중 모드에서 듣는 중이었으면 새 카드에서도 이어서 듣고, 멈춰 있었으면 멈춘 채로 넘긴다
  // (말하기 모드는 넘기면 늘 새 용어를 들려준다)
  const move = (step) => {
    if (state.mode === "walk" && !isPlaying()) state.hold = true;
    clearTimeout(state.nextTimer);
    state.nextTimer = null;
    goTo(index + step);
  };

  const prev = h("button", { class: "ctrl", type: "button", "aria-label": t("walk.prev"), onclick: () => move(-1) }, icon("prev"));
  const main = h("button", { class: "ctrl main", type: "button", onclick: toggle });
  const next = h("button", { class: "ctrl", type: "button", "aria-label": t("walk.next"), onclick: () => move(1) }, icon("next"));
  prev.disabled = !hasPrev;
  next.disabled = !hasNext;
  if (!speech.supported) main.disabled = true;

  function paint() {
    const playing = isPlaying();
    const paused = speech.owner === "all" && speech.status === "paused";
    main.classList.toggle("playing", playing);
    main.classList.toggle("paused", paused);
    main.setAttribute("aria-pressed", String(playing));
    main.replaceChildren(
      icon(playing ? "pause" : paused ? "play" : "speaker"),
      h("span", {}, playing ? t("speak.pause") : paused ? t("speak.resume") : t("speak.all"))
    );
    syncWakeLock();
  }
  speech.listeners.add(paint);
  paint();

  const bar = h("nav", { class: "bottom-bar", "aria-label": t("controls.label") },
    h("div", { class: "bottom-inner" }, prev, main, next));
  return { bar, toggle, playFull, isPlaying };
}

/* ---------- 듣기 (Web Speech API의 speechSynthesis) ---------- */

// 영어 음성이 없을 때: 문장 속 영어 용어 이름을 한글 발음으로 바꾼다.
// 긴 이름부터 바꿔야 "OAuth2"가 "OAuth"보다 먼저 처리된다.
function toKoreanSounds(text) {
  const names = state.terms
    .map((term) => [term.term_en, term.pronunciation.ko])
    .sort((a, b) => b[0].length - a[0].length);
  return names.reduce((s, [en, ko]) => s.replaceAll(en, ko), text);
}

const speech = {
  supported: "speechSynthesis" in window,

  // 그 언어의 음성 중 "가장 좋은" 것을 고른다. 기기마다 들어 있는 음성이 다르다.
  // 목록의 첫 번째는 보통 오래된 기본 음성이라, 이름으로 고품질 음성을 찾아 점수를 매긴다.
  //   Natural·Neural: 신경망 음성 (엣지의 "SunHi Online (Natural)" 등) → 가장 자연스럽다
  //   Online·Google: 인터넷으로 만드는 음성 (크롬의 "Google 한국의" 등)
  //   Enhanced·Premium: 아이폰의 고품질 음성
  voiceFor(lang) {
    const prefix = lang.slice(0, 2);
    const candidates = speechSynthesis.getVoices().filter((v) => v.lang.replace("_", "-").startsWith(prefix));
    const score = (v) =>
      (/natural|neural/i.test(v.name) ? 100 : 0) +
      (/online/i.test(v.name) ? 60 : 0) +
      (/google/i.test(v.name) ? 50 : 0) +
      (/enhanced|premium/i.test(v.name) ? 40 : 0) +
      (v.lang.replace("_", "-") === lang ? 5 : 0);
    return candidates.sort((a, b) => score(b) - score(a))[0];
  },

  // 읽기 전에 기호를 정리한다. 괄호·화살표·가운뎃점을 음성이 어색하게 끊어 읽기 때문이다.
  // 예: "Proof(증명) of Concept(개념) → 개념 증명" → "Proof 증명 of Concept 개념, 개념 증명"
  clean(text) {
    return text
      // 괄호 바로 뒤에 한글(조사)이 붙으면 괄호 속 말은 빼고 읽는다: "위험(리스크)을" → "위험을"
      .replace(/\([^)]*\)(?=[가-힣])/g, "")
      .replace(/\s*(→|->)\s*/g, ", ")
      .replace(/\s*[·•]\s*/g, ", ")
      .replace(/[()[\]]/g, " ")
      .replace(/['"‘’“”]/g, "")
      .replace(/\s*\/\s*/g, ", ")
      .replace(/\s{2,}/g, " ")
      .replace(/\s+([,.])/g, "$1")   // 쉼표·마침표 앞 빈칸 지우기
      .trim();
  },

  // ----- 재생 상태 -----
  // 버튼 하나로 재생 ↔ 일시정지를 오간다. 일시정지 후 다시 누르면 멈춘 문장부터 이어서 읽는다.
  // (브라우저의 speechSynthesis.pause()는 휴대폰에서 잘 안 되는 경우가 많아, 문장 번호를 기억해 직접 이어 읽는다)
  owner: null,          // 지금 재생 중인 버튼: "term"(발음) 또는 "all"(전체)
  status: "idle",       // idle(멈춤) / playing(재생 중) / paused(일시정지)
  queue: [],            // 읽을 문장 목록 [{ text, lang, sec }]
  index: 0,             // 지금 읽는 문장 번호
  token: 0,             // 재생을 새로 시작하거나 멈출 때마다 바뀐다. 이전 재생의 남은 문장이 이어지지 않게 한다
  timer: null,
  onFinish: null,       // 끝까지 다 읽었을 때 부를 함수 (이동 중 모드의 다음 카드 넘기기)
  onSentence: null,     // 문장을 읽기 시작할 때 부를 함수 (읽는 구역 색칠)
  listeners: new Set(), // 상태가 바뀌면 버튼 모양을 다시 그리는 함수들

  toggle(owner, makeParts) {
    if (this.owner === owner && this.status === "playing") return this.pause();
    if (this.owner === owner && this.status === "paused") return this.run(this.index);
    this.start(owner, makeParts());
  },

  start(owner, parts, onFinish) {
    this.stop();
    this.owner = owner;
    this.onFinish = onFinish ?? null;
    this.queue = parts.flatMap((p) =>
      p.pause ? [p] : this.sentences(p.text, p.lang).map((s) => ({ text: s, lang: p.lang, sec: p.sec }))
    );
    this.run(0);
  },

  // from번째 문장부터 한 문장씩 읽는다. 한 문장이 끝나면(onend) 다음 문장을 읽는다.
  //
  // 휴대폰 브라우저에서 생기는 문제와 대비 (2026-11-11, "전체 듣기가 안 된다" 신고)
  //  ① 고른 음성이 그 기기에서 안 되는 경우 → 오류가 나거나 소리 없이 끝난다
  //     → 음성을 지정하지 않고(기기 기본 음성) 같은 문장을 한 번 더 읽고, 그 뒤로는 기본 음성만 쓴다
  //  ② 문장이 끝나도 끝 신호(onend)가 오지 않는 경우 → 다음 문장으로 안 넘어가 멈춘 것처럼 보인다
  //     → 0.5초마다 "지금 말하는 중인지" 직접 확인해서, 말이 끝났으면 다음 문장으로 넘긴다 (감시 타이머)
  //  ③ 아이폰은 버튼을 누른 그 순간에 한 번 말을 시작해야 그 뒤 소리를 허락한다
  //     → 버튼을 누를 때 빈 문장을 먼저 말해서 잠금을 푼다
  //  ④ 소리가 "일시정지"에 걸린 채 남아 있는 경우(크롬) → 말하기 전에 resume()을 부른다
  run(from) {
    if (!this.supported) return;
    this.halt();
    const myToken = this.token;
    this.setStatus("playing");
    this.unlock();

    const next = (i) => {
      if (myToken !== this.token) return;     // 그사이 멈췄거나 다른 재생이 시작됨
      clearInterval(this.watch);
      this.index = i;
      if (i >= this.queue.length) {           // 다 읽음
        const done = this.onFinish;
        this.owner = null;
        this.onFinish = null;
        this.setStatus("idle");
        done?.();
        return;
      }
      const p = this.queue[i];
      this.onSentence?.(p);
      if (p.pause) { this.timer = setTimeout(() => next(i + 1), p.pause); return; }
      say(p, i, false);
    };

    const say = (p, i, isRetry) => {
      const u = new SpeechSynthesisUtterance(p.text);
      u.lang = p.lang;
      const voice = this.useDefaultVoice ? null : this.voiceFor(p.lang);
      if (voice) u.voice = voice;
      u.rate = 0.95;

      let started = false;
      let finished = false;
      const sentAt = Date.now();
      const finish = () => { if (!finished) { finished = true; next(i + 1); } };
      const fail = (reason) => {
        if (finished || myToken !== this.token) return;
        this.lastError = reason;
        // ① 지정한 음성으로 실패했으면 기본 음성으로 한 번 더
        if (voice && !isRetry) {
          finished = true;
          this.useDefaultVoice = true;
          clearInterval(this.watch);
          speechSynthesis.cancel();
          say(p, i, true);
          return;
        }
        finish();
      };
      u.onstart = () => { started = true; };
      u.onend = () => (started || Date.now() - sentAt > 300 ? finish() : fail("소리 없이 끝남"));
      u.onerror = (e) => {
        if (e.error === "interrupted" || e.error === "canceled") return;   // 우리가 멈춘 것
        fail(e.error || "오류");
      };

      speechSynthesis.resume();               // ④
      speechSynthesis.speak(u);

      // ② 감시 타이머: 끝 신호가 안 와도 다음 문장으로 넘어가게 한다
      clearInterval(this.watch);
      this.watch = setInterval(() => {
        if (finished || myToken !== this.token) { clearInterval(this.watch); return; }
        const waited = Date.now() - sentAt;
        const busy = speechSynthesis.speaking || speechSynthesis.pending;
        if (!started && !busy && waited > 1500) fail("시작되지 않음");
        else if (started && !busy && waited > 800) finish();
        else if (!started && waited > 4000) fail("시작되지 않음");
      }, 500);
    };

    next(from);
  },

  // ③ 아이폰 잠금 풀기: 버튼을 누른 순간에 빈 문장을 한 번 말한다
  unlock() {
    if (this.unlocked) return;
    this.unlocked = true;
    try {
      const u = new SpeechSynthesisUtterance(" ");
      u.volume = 0;
      speechSynthesis.speak(u);
    } catch { /* 무시 */ }
  },

  useDefaultVoice: false, // 고른 음성이 이 기기에서 안 되면 true (그 뒤로는 기기 기본 음성)
  unlocked: false,
  watch: null,
  lastError: "",          // 정보 화면에 보여 줄 마지막 음성 오류 (문제 신고용)

  pause() { this.halt(); this.setStatus("paused"); },

  stop() {
    this.halt();
    this.owner = null;
    this.onFinish = null;
    this.queue = [];
    this.index = 0;
    this.setStatus("idle");
  },

  // 지금 나오는 소리와 예약된 쉬기를 모두 끊는다
  halt() {
    this.token += 1;
    clearTimeout(this.timer);
    clearInterval(this.watch);
    if (this.supported) speechSynthesis.cancel();
  },

  setStatus(status) {
    this.status = status;
    this.listeners.forEach((fn) => fn());
  },

  // 기호를 정리하고 문장 단위로 나눈다. 긴 문단을 나누는 이유: 일부 브라우저는 15초가 넘는 문장을 중간에 끊는다.
  sentences(text, lang) {
    let s = this.clean(text);
    if (lang.startsWith("ko")) s = fixKoreanSpeech(koreanCounters(s));
    // 문장 끝(. ? !) 뒤의 빈칸에서 나눈다. (오래된 아이폰은 "뒤를 보는 정규식"을 몰라서 쓰지 않는다)
    return s.replace(/([.?!])\s+/g, "$1\n").split("\n").map((x) => x.trim()).filter(Boolean);
  },
};

// 숫자 + 세는 말은 고유어 숫자로 읽어야 자연스럽다: "3번" → "세 번", "10명 중 6명" → "열 명 중 여섯 명"
// (음성은 숫자를 "삼 번"처럼 한자어로 읽는다. "2주", "40%"처럼 한자어로 읽는 것은 그대로 둔다)
const NATIVE_ONES = ["", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉"];
const NATIVE_TENS = ["", "열", "스물", "서른", "마흔", "쉰", "예순", "일흔", "여든", "아흔"];
function nativeNumber(n) {
  if (n === 20) return "스무";
  const tens = Math.floor(n / 10), ones = n % 10;
  return NATIVE_TENS[tens] + NATIVE_ONES[ones];
}
// 음성 엔진이 잘못 읽는 낱말 고침표. 화면 글자는 그대로 두고, 소리로 읽을 때만 바꾼다.
// 기기마다 음성 엔진이 달라서 생기는 문제라, 신고가 들어온 낱말만 하나씩 추가한다.
//   2026-11-11 "어댑터"를 "어댐터"로 읽음 (사용자 휴대폰) → 띄어 읽게 해서 받침 ㅂ이 ㅁ으로 바뀌지 않게 한다
const SPEECH_FIXES = [
  [/어댑터/g, "어댑 터"],
];
function fixKoreanSpeech(text) {
  return SPEECH_FIXES.reduce((s, [from, to]) => s.replace(from, to), text);
}

function koreanCounters(text) {
  return text.replace(/(\d{1,2})\s?(번|개|명|장|시간|가지|달|군데|살|마리|권)/g,
    (all, num, unit) => {
      const n = Number(num);
      return n >= 1 && n <= 99 ? `${nativeNumber(n)} ${unit}` : all;
    });
}

// ----- 읽을 문장 만들기 -----
// 각 문장에 sec(카드의 어느 구역인지)을 붙여, 읽는 중인 구역에 색을 칠할 수 있게 한다.

// 영어 음성이 없는 기기도 있다(예: 한국어 음성만 깔린 윈도우).
// 그때 한국어 음성이 영어 철자를 읽으면 어색하므로, 한글 발음 표기를 대신 읽는다.
// 음성 목록은 늦게 준비되는 브라우저가 있어서 읽을 때마다 확인한다.
const hasEnglishVoice = () => Boolean(speech.voiceFor("en-US"));

function termPart(term) {
  return hasEnglishVoice()
    ? { text: englishSay(term), lang: "en-US", sec: "term" }
    : { text: term.pronunciation.ko, lang: "ko-KR", sec: "term" };
}

// 영어 음성에게 줄 글자.
// 한 글자씩 읽는 약어(read_as: "letters")는 글자 사이를 띄워 준다: "PoC" → "P O C"
// 그대로 주면 영어 음성이 단어로 읽어 버린다 ("PoC" → "폭")
function englishSay(term) {
  const p = term.pronunciation;
  if (p.tts) return p.tts;
  if (p.read_as === "letters") return term.term_en.toUpperCase().replace(/[^A-Z0-9]/g, "").split("").join(" ");
  return term.term_en;
}

function termOnlyParts(term) { return [termPart(term)]; }

// 전체 듣기 순서: 화면 위에서 아래로 보이는 순서와 같다.
// 면접 질문 뒤에는 3초 쉬어서, 답을 듣기 전에 먼저 떠올려 보게 한다 (인출 연습).
function fullParts(term) {
  const hasEnglish = hasEnglishVoice();

  // 한국어 문장 속 영어 용어(예: "OAuth로 붙이면", "MVP는")도 영어 음성이 없으면 한글 발음으로 바꿔 읽는다.
  const ko = (text, sec) => ({ text: hasEnglish ? text : toKoreanSounds(text), lang: "ko-KR", sec });

  // 다른 용어 이름을 한국어 문장 안에서 읽을 때는 한글 발음으로 읽는다. (예: "엠브이피")
  const sayName = (id) => state.allById.get(id)?.pronunciation.ko;

  const pairs = state.pairs.filter((p) => p.a === term.id || p.b === term.id);
  const related = (term.related ?? []).map(sayName).filter(Boolean);

  // 약어 풀이는 화살표 뒤 우리말 부분만 읽는다. ("Proof(증명) of …" 같은 영어 단어를 한국어 음성이 읽으면 어색하다)
  // 예: "Proof(증명) of Concept(개념) → 개념 증명. 우리말로는…" → "개념 증명. 우리말로는…"
  const expansionKo = term.expansion_ko?.split("→").pop().trim();

  return [
    termPart(term),
    term.expansion && hasEnglish && { text: term.expansion, lang: "en-US", sec: "expansion" },
    expansionKo && ko(expansionKo, "expansion"),
    ko(`${t("speak.def_prefix")} ${term.definition}`, "def"),
    term.analogy && ko(`${t("speak.analogy_prefix")} ${term.analogy}`, "analogy"),
    ...term.examples.map((ex, i) => ko(`${t(`context.${ex.context}`)}. ${ex.sentence}`, `ex-${i}`)),
    term.pitfall && ko(`${t("card.pitfall")}. ${term.pitfall}`, "pitfall"),
    ...pairs.map((p) => {
      const otherId = p.a === term.id ? p.b : p.a;
      return ko(`${t("speak.pair", { name: sayName(otherId) })}. ${t("card.pair.diff")}. ${p.difference}`, "pair");
    }),
    term.interview_q && ko(`${t("card.interview")}. ${term.interview_q}`, "interview"),
    term.interview_q && term.interview_a && { pause: 3000, sec: "interview" },
    term.interview_a && ko(`${t("speak.answer_prefix")}. ${term.interview_a}`, "answer"),
    related.length > 0 && ko(`${t("card.related")}. ${related.join(", ")}.`, "related"),
  ].filter(Boolean);
}

// 듣기 버튼 하나 = 재생 ↔ 일시정지 토글. (카드 제목 옆의 작은 "발음" 버튼에 쓴다)
// 아이콘은 "지금 누르면 일어날 일"을 보여 준다. 음악 앱·유튜브와 같은 약속이다.
function speakButton(key, label, makeParts, size = "") {
  const btn = h("button", { class: `btn speak-btn ${size}`, type: "button", onclick: () => speech.toggle(key, makeParts) });
  const render = () => {
    const mine = speech.owner === key;
    const playing = mine && speech.status === "playing";
    const paused = mine && speech.status === "paused";
    btn.classList.toggle("playing", playing);
    btn.classList.toggle("paused", paused);
    btn.setAttribute("aria-pressed", String(playing));
    btn.replaceChildren(icon(playing ? "pause" : paused ? "play" : "speaker"), label);
  };
  speech.listeners.add(render);
  render();
  return btn;
}

// 직접 그린 작은 아이콘(SVG). 이모지는 기기마다 모양과 색이 달라 흐리게 보일 수 있다.
// 선 색을 currentColor로 두면 버튼 글자색을 그대로 따라가서, 어두운 버튼·다크 모드에서도 선명하다.
const ICONS = {
  speaker: "M4 9v6h4l5 4V5L8 9H4z M16 8.5a5 5 0 0 1 0 7 M18.5 6a8.5 8.5 0 0 1 0 12",
  play: "M8 5v14l11-7z",
  pause: "M8 5v14 M16 5v14",
  prev: "M6 5v14 M18 5l-9 7 9 7z",
  next: "M18 5v14 M6 5l9 7-9 7z",
  walk: "M13 4a1.5 1.5 0 1 0 0 .01 M10 21l2-6 3 3v3 M12 15l-1-5 4 2 3 1 M11 10l-3 2-1 3",
};
function icon(name) {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("class", "icon");
  const path = document.createElementNS(ns, "path");
  path.setAttribute("d", ICONS[name]);
  svg.append(path);
  return svg;
}

/* ---------- 화면 켜 두기 · 잠금 화면 조작 ---------- */

// 화면 켜 두기(Wake Lock API): 화면이 꺼지면 브라우저가 읽기를 멈추기 때문에,
// 🚶 이동 중 모드에서 듣는 동안에만 화면을 켜 둔다. 배터리 절약 모드 등에서는 거절될 수 있다.
let wakeLock = null;
function syncWakeLock() {
  const want = state.mode === "walk" && (speech.status === "playing" || state.nextTimer !== null);
  keepScreenOn(want);
}
async function keepScreenOn(on) {
  if (!("wakeLock" in navigator)) return;
  try {
    if (on && !wakeLock) {
      wakeLock = await navigator.wakeLock.request("screen");
      wakeLock.addEventListener("release", () => { wakeLock = null; });
    } else if (!on && wakeLock) {
      await wakeLock.release();
      wakeLock = null;
    }
  } catch { /* 무시 */ }
}
// 다른 앱에 갔다 돌아오면 화면 켜 두기가 풀려 있으므로 다시 건다
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") syncWakeLock();
});

// 잠금 화면·이어폰 버튼 연결 (Media Session API). 지원하는 기기에서만 동작한다.
const MEDIA_ACTIONS = ["play", "pause", "nexttrack", "previoustrack"];
function updateMediaSession(term, toggle, next, prev) {
  if (!("mediaSession" in navigator)) return;
  try {
    navigator.mediaSession.metadata = new MediaMetadata({
      title: `${term.term_en} · ${term.term_ko}`,
      artist: t("app.name"),
      album: t(`stage.${term.stage}`),
    });
    navigator.mediaSession.setActionHandler("play", toggle);
    navigator.mediaSession.setActionHandler("pause", toggle);
    navigator.mediaSession.setActionHandler("nexttrack", next);
    navigator.mediaSession.setActionHandler("previoustrack", prev);
  } catch { /* 일부 동작을 지원하지 않는 브라우저 */ }
}
function clearMediaSession() {
  if (!("mediaSession" in navigator)) return;
  navigator.mediaSession.metadata = null;
  for (const a of MEDIA_ACTIONS) { try { navigator.mediaSession.setActionHandler(a, null); } catch { /* 무시 */ } }
}

/* ---------- 화면 3: 정보 ---------- */

/* ---------- 화면 4: 의견 보내기 ---------- */
// 이름·전화번호 같은 개인정보는 받지 않는다. 답장을 원할 때만 이메일을 선택으로 적는다.
const FEEDBACK_KINDS = ["wrong", "confusing", "add", "app", "etc"];

function renderFeedback(termId) {
  renderTopbar("card");
  document.body.classList.add("no-footer");
  const term = termId ? state.allById.get(termId) : null;

  const kind = h("select", { id: "fb-kind", name: "kind" },
    FEEDBACK_KINDS.map((k) => h("option", { value: k }, t(`fb.kind.${k}`))));
  const about = h("input", { id: "fb-term", name: "term", type: "text", placeholder: t("fb.term.ph"), value: term ? term.term_en : "" });
  const message = h("textarea", { id: "fb-message", name: "message", rows: "6", placeholder: t("fb.message.ph") });
  const email = h("input", { id: "fb-email", name: "email", type: "email", placeholder: "name@example.com", autocomplete: "email" });
  // 사람에게는 보이지 않는 칸. 자동으로 글을 올리는 프로그램(스팸 봇)만 채운다 → 채워져 있으면 버린다 (허니팟)
  const trap = h("input", { name: "botcheck", type: "checkbox", tabindex: "-1", class: "hp", "aria-hidden": "true" });
  const error = h("p", { class: "field-error", role: "alert" });
  const status = h("div", { role: "status" });
  const send = h("button", { class: "btn primary", type: "submit" }, t("fb.send"));

  message.addEventListener("input", () => { error.textContent = ""; });

  const form = h("form", { class: "fb-form", novalidate: "" },
    field("fb-kind", t("fb.kind"), kind),
    field("fb-term", t("fb.term"), about),
    field("fb-message", t("fb.message"), message, error),
    field("fb-email", t("fb.email"), email, h("p", { class: "muted" }, t("fb.email.help"))),
    trap,
    h("p", { class: "muted" }, t("fb.privacy")),
    send,
    status
  );

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = message.value.trim();
    if (!text) { error.textContent = t("fb.error.empty"); message.focus(); return; }
    if (trap.checked) return;

    const data = {
      kind: t(`fb.kind.${kind.value}`),
      term: about.value.trim(),
      message: text,
      email: email.value.trim(),
    };

    // 키가 아직 없으면: 메일 앱을 열어 내용을 채워 준다
    if (!FEEDBACK.accessKey) {
      location.href = mailtoLink(data);
      status.replaceChildren(h("p", { class: "notice" }, t("fb.mailto.opened")));
      return;
    }

    send.disabled = true;
    send.textContent = t("fb.sending");
    try {
      const res = await fetch(FEEDBACK.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          access_key: FEEDBACK.accessKey,
          subject: `[필드워드 의견] ${data.kind}${data.term ? ` · ${data.term}` : ""}`,
          from_name: "필드워드 앱",
          종류: data.kind,
          관련_용어: data.term || "-",
          내용: data.message,
          email: data.email || undefined,   // 적었으면 받은 메일에서 바로 '답장'할 수 있다
          botcheck: false,
        }),
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.message);
      form.replaceWith(h("div", { class: "notice" }, h("p", {}, t("fb.done"))));
    } catch {
      send.disabled = false;
      send.textContent = t("fb.send");
      status.replaceChildren(h("p", { class: "field-error" }, t("fb.error.send"), " ",
        h("a", { href: mailtoLink(data) }, t("fb.error.mailto"))));
    }
  });

  app.replaceChildren(h("article", { class: "card" },
    h("h1", {}, t("fb.title")),
    h("p", { class: "muted" }, t("fb.intro")),
    form
  ));
}

function field(id, label, control, ...extra) {
  return h("div", { class: "field" }, h("label", { for: id }, label), control, ...extra);
}

function mailtoLink(d) {
  const subject = `[필드워드 의견] ${d.kind}${d.term ? ` · ${d.term}` : ""}`;
  const body = `종류: ${d.kind}\n관련 용어: ${d.term || "-"}\n\n${d.message}\n`;
  return `mailto:${FEEDBACK.mailto}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

function renderAbout() {
  renderTopbar("card");
  document.body.classList.add("no-footer");   // 이 화면이 곧 "정보"라서 아래 링크는 숨긴다
  app.replaceChildren(
    h("article", { class: "card" },
      h("h1", {}, t("about.title")),
      section(null, t("about.data.title"),
        h("div", { class: "notice" },
          h("p", {}, t("about.data.body1")),
          h("p", {}, t("about.data.body2")),
          h("p", {}, t("about.data.body3"))
        )
      ),
      section(null, t("about.feedback"),
        h("p", {}, t("about.feedback.body")),
        h("p", {}, h("a", { class: "btn primary", href: "#/feedback" }, t("about.feedback")))
      ),
      section(null, t("about.oss.title"), h("p", {}, t("about.oss.body"))),
      section(null, t("about.voice"), voiceInfo()),
      section(null, t("about.version"), h("p", { class: "muted" }, `v${APP_VERSION} · ${t("about.count", { n: state.terms.length })}`))
    )
  );
}

// 이 기기에서 실제로 쓰는 음성 이름. 소리 품질을 비교하거나 문제를 찾을 때 본다.
// 음성 목록은 늦게 준비되는 브라우저가 있어서, 준비되면 다시 채운다.
function voiceInfo() {
  const box = h("p", { class: "muted" });
  const fill = () => {
    if (!speech.supported) { box.textContent = t("speak.unsupported"); return; }
    const ko = speech.voiceFor("ko-KR");
    const en = speech.voiceFor("en-US");
    box.replaceChildren(
      h("span", {}, `${t("about.voice.ko")}: ${ko ? ko.name : t("about.voice.none")}`), h("br"),
      h("span", {}, `${t("about.voice.en")}: ${en ? en.name : t("about.voice.none")}`),
      // 문제 신고용: 이 기기에서 음성이 실패한 적이 있으면 그 이유를 보여 준다
      speech.useDefaultVoice ? h("span", {}, h("br"), t("about.voice.fallback")) : "",
      speech.lastError ? h("span", {}, h("br"), `${t("about.voice.error")}: ${speech.lastError}`) : ""
    );
  };
  fill();
  if (speech.supported) speechSynthesis.addEventListener("voiceschanged", fill, { once: true });
  return box;
}

/* ---------- 화면: 내 기록 (성장 대시보드) ---------- */
// 지난날 무엇을 공부했고 얼마나 늘었는지 보여 준다. 데이터는 이 브라우저의 일지(Review.stats)뿐이다.

const SVG_NS = "http://www.w3.org/2000/svg";
function sv(tag, attrs = {}, ...children) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v != null) el.setAttribute(k, v);
  for (const c of children.flat()) if (c != null && c !== false) el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return el;
}
const shortDate = (d) => `${Number(d.slice(5, 7))}/${Number(d.slice(8, 10))}`;

function renderProgress() {
  renderTopbar("card");
  const s = Review.stats(state.terms);
  const nameOf = (id) => state.allById.get(id)?.term_en ?? id;

  const tile = (value, label, sub) =>
    h("div", { class: "stat-tile" }, h("span", { class: "stat-value" }, value), h("span", { class: "stat-label" }, label),
      sub ? h("span", { class: "stat-sub" }, sub) : "");

  const tiles = h("div", { class: "stat-tiles" },
    tile(s.studyDays, t("prog.days"), s.firstDate ? t("prog.since", { d: shortDate(s.firstDate) }) : ""),
    tile(s.streak, t("prog.streak")),
    tile(`${s.seenTerms}`, t("prog.seen"), t("prog.of", { n: state.terms.length })),
    tile(`🏅 ${s.longTerm}`, t("prog.longterm"), t("prog.longterm.sub")),
    tile(s.totalCorrected, t("prog.corrected"), t("prog.misconceptions", { n: s.totalMisconceptions }))
  );

  if (!s.studyDays) {
    app.replaceChildren(h("article", { class: "card" }, h("h1", {}, t("prog.title")), tiles,
      h("p", { class: "muted" }, t("prog.empty")), backupSection()));
    return;
  }

  const days = h("div", { class: "day-list" });
  const openDay = (date) => {
    const el = days.querySelector(`[data-date="${date}"]`);
    if (!el) return;
    el.hidden = false;
    el.open = true;
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  app.replaceChildren(
    h("article", { class: "card progress" },
      h("h1", {}, t("prog.title")),
      tiles,
      section(null, t("prog.heat.title"), heatmap(s, openDay)),
      section(null, t("prog.growth.title"), growthChart(s)),
      section(null, t("prog.stage.title"), stageBars(s)),
      section(null, t("prog.days.title"), days),
      backupSection()
    )
  );

  // 날짜별 기록: 최근 날짜가 위로. 첫 날짜만 펼쳐 둔다. 처음엔 30일만, 나머지는 "더 보기"로.
  const SHOW = 30;
  const allDates = [...s.dates].reverse();
  if (allDates.length > SHOW) {
    const more = h("button", { class: "btn small", type: "button", onclick: () => {
      days.querySelectorAll(".day[hidden]").forEach((el) => { el.hidden = false; });
      more.remove();
    } }, t("prog.days.more", { n: allDates.length - SHOW }));
    queueMicrotask(() => days.after(more));
  }
  allDates.forEach((date, k) => {
    const d = s.log[date];
    const mark = (id) => [
      d.new.includes(id) && t("prog.mark.new"),
      d.misconceptions.includes(id) ? t("prog.mark.misconception") : d.wrong.includes(id) && t("prog.mark.wrong"),
      d.corrected.includes(id) && t("prog.mark.corrected"),
      d.long_term.includes(id) && "🏅",
    ].filter(Boolean).join(" ");
    days.append(h("details", { class: "day", "data-date": date, open: k === 0 ? "" : undefined, hidden: k >= SHOW ? "" : undefined },
      h("summary", {}, h("strong", {}, date), " ",
        h("span", { class: "muted" }, t("prog.day.sum", { n: d.seen.length, f: d.new.length, w: d.wrong.length }))),
      h("div", { class: "day-terms" },
        d.seen.map((id) => h("a", { class: `day-term${d.corrected.includes(id) ? " corrected" : ""}`, href: `#/term/${encodeURIComponent(id)}` },
          nameOf(id), mark(id) ? h("span", { class: "day-mark" }, mark(id)) : "")))
    ));
  });
}

// 잔디: 최근 12주, 하루 한 칸. 진할수록 많이 본 날. 칸을 누르면 그날 기록으로 내려간다.
function heatmap(s, openDay) {
  const WEEKS = 12, CELL = 14, GAP = 3, LEFT = 22, TOP = 16;
  const today = Review.today();
  const [y, m, d] = today.split("-").map(Number);
  const dow = (new Date(y, m - 1, d).getDay() + 6) % 7;          // 월=0 … 일=6
  const start = Review.addDays(today, -(dow + 7 * (WEEKS - 1)));  // 12주 전 월요일
  const level = (n) => (n === 0 ? 0 : n < 5 ? 1 : n < 10 ? 2 : n < 20 ? 3 : 4);

  const width = LEFT + WEEKS * (CELL + GAP), height = TOP + 7 * (CELL + GAP);
  const svg = sv("svg", { viewBox: `0 0 ${width} ${height}`, class: "heat", role: "img",
    "aria-label": t("prog.heat.aria", { n: s.studyDays }) });
  ["월", "수", "금"].forEach((label, k) =>
    svg.append(sv("text", { x: 0, y: TOP + k * 2 * (CELL + GAP) + CELL - 3, class: "axis-text" }, label)));

  for (let w = 0; w < WEEKS; w++) {
    for (let r = 0; r < 7; r++) {
      const date = Review.addDays(start, w * 7 + r);
      if (date > today) continue;
      if (r === 0 && (w === 0 || date.slice(8) <= "07")) {
        svg.append(sv("text", { x: LEFT + w * (CELL + GAP), y: 10, class: "axis-text" }, `${Number(date.slice(5, 7))}월`));
      }
      const n = s.log[date]?.seen.length ?? 0;
      const cell = sv("rect", {
        x: LEFT + w * (CELL + GAP), y: TOP + r * (CELL + GAP), width: CELL, height: CELL, rx: 3,
        class: `heat-${level(n)}${date === today ? " heat-today" : ""}`,
      }, sv("title", {}, t("prog.heat.cell", { d: date, n })));
      if (n) { cell.style.cursor = "pointer"; cell.addEventListener("click", () => openDay(date)); }
      svg.append(cell);
    }
  }
  const legend = h("div", { class: "heat-legend muted" }, t("prog.heat.less"),
    [0, 1, 2, 3, 4].map((k) => h("span", { class: `heat-swatch heat-${k}` })), t("prog.heat.more"));
  return h("div", {}, h("div", { class: "heat-wrap" }, svg), legend);
}

// 성장 그래프: 날짜별 누적 "본 용어"와 "🏅 장기 기억". 축은 하나(같은 단위: 용어 수).
function growthChart(s) {
  const pts = s.cumulative;
  if (pts.length < 2) return h("p", { class: "muted" }, t("prog.growth.wait"));

  const W = 360, H = 200, L = 30, R = 84, T = 12, B = 24;   // 휴대폰 폭(약 360px)에서 글자가 실제 크기로 보이게
  const first = new Date(pts[0].date), last = new Date(pts.at(-1).date);
  const span = Math.max(last - first, 1);
  const x = (date) => L + ((new Date(date) - first) / span) * (W - L - R);
  // 세로축 눈금은 읽기 쉬운 숫자로 4칸 (예: 0·25·50·75·100)
  const max = Math.max(...pts.map((p) => p.seen));
  const step = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500].find((n) => n * 4 >= max) ?? Math.ceil(max / 4);
  const top = step * 4;
  const y = (v) => T + (1 - v / top) * (H - T - B);

  const svg = sv("svg", { viewBox: `0 0 ${W} ${H}`, class: "growth", role: "img",
    "aria-label": t("prog.growth.aria", { s: pts.at(-1).seen, l: pts.at(-1).longTerm }) });
  for (let k = 0; k <= 4; k++) {
    const v = (top / 4) * k;
    svg.append(sv("line", { x1: L, x2: W - R, y1: y(v), y2: y(v), class: k ? "grid" : "baseline" }));
    svg.append(sv("text", { x: L - 6, y: y(v) + 4, class: "axis-text", "text-anchor": "end" }, Math.round(v)));
  }
  svg.append(sv("text", { x: L, y: H - 6, class: "axis-text" }, shortDate(pts[0].date)));
  svg.append(sv("text", { x: W - R, y: H - 6, class: "axis-text", "text-anchor": "end" }, shortDate(pts.at(-1).date)));

  const series = [
    { key: "seen", cls: "line-seen", label: t("prog.seen") },
    { key: "longTerm", cls: "line-long", label: t("prog.longterm") },
  ];
  for (const sr of series) {
    const d = pts.map((p, k) => `${k ? "L" : "M"}${x(p.date).toFixed(1)},${y(p[sr.key]).toFixed(1)}`).join(" ");
    svg.append(sv("path", { d, class: `line ${sr.cls}` }));
    const end = pts.at(-1);
    svg.append(sv("circle", { cx: x(end.date), cy: y(end[sr.key]), r: 4, class: `dot ${sr.cls}` }));
    svg.append(sv("text", { x: x(end.date) + 8, y: y(end[sr.key]) + 4, class: "end-label" }, `${sr.label} ${end[sr.key]}`));
  }

  // 마우스·손가락을 올리면 가장 가까운 날짜의 숫자를 보여 준다
  const guide = sv("line", { y1: T, y2: H - B, class: "guide", visibility: "hidden" });
  const tip = h("div", { class: "chart-tip", hidden: "" });
  svg.append(guide);
  const wrap = h("div", { class: "growth-wrap" }, svg, tip);
  const show = (ev) => {
    const box = svg.getBoundingClientRect();
    const px = ((ev.clientX - box.left) / box.width) * W;
    const p = pts.reduce((a, b) => (Math.abs(x(b.date) - px) < Math.abs(x(a.date) - px) ? b : a));
    guide.setAttribute("x1", x(p.date)); guide.setAttribute("x2", x(p.date)); guide.setAttribute("visibility", "visible");
    tip.replaceChildren(h("strong", {}, p.date), h("br"), `${t("prog.seen")} ${p.seen}`, h("br"), `${t("prog.longterm")} ${p.longTerm}`);
    tip.hidden = false;
    tip.style.left = `${Math.max(0, Math.min((x(p.date) / W) * box.width + 12, box.width - 150))}px`;
  };
  svg.addEventListener("pointermove", show);
  svg.addEventListener("pointerdown", show);
  svg.addEventListener("pointerleave", () => { guide.setAttribute("visibility", "hidden"); tip.hidden = true; });

  const legend = h("div", { class: "chart-legend" },
    series.map((sr) => h("span", {}, h("span", { class: `legend-swatch ${sr.cls}` }), sr.label)));
  return h("div", {}, legend, wrap);
}

// 단계별 진행: 단계마다 "본 용어 / 전체". 막대 하나 = 한 단계
function stageBars(s) {
  return h("div", { class: "stage-bars" }, STAGES.map((stage) => {
    const b = s.byStage[stage] ?? { total: 0, seen: 0, longTerm: 0 };
    const pct = b.total ? Math.round((b.seen / b.total) * 100) : 0;
    return h("div", { class: "stage-bar" },
      h("span", { class: "stage-name" }, t(`stage.${stage}`)),
      h("span", { class: "bar-track", role: "img", "aria-label": `${b.seen} / ${b.total}` },
        h("span", { class: "bar-fill", style: `width:${pct}%` })),
      h("span", { class: "stage-num" }, `${b.seen}/${b.total}${b.longTerm ? ` · 🏅${b.longTerm}` : ""}`));
  }));
}

// 기록 백업: 브라우저 데이터를 지우거나 휴대폰을 바꿔도 이어서 쓸 수 있게 파일로 보관
function backupSection() {
  const msg = h("p", { class: "muted", "aria-live": "polite" });
  const save = () => {
    const blob = new Blob([JSON.stringify(Review.exportAll())], { type: "application/json" });
    const a = h("a", { href: URL.createObjectURL(blob), download: `fieldwords-backup-${Review.today()}.json` });
    document.body.append(a); a.click(); a.remove();
    msg.textContent = t("prog.backup.saved");
  };
  const input = h("input", { type: "file", accept: "application/json,.json", hidden: "" });
  input.addEventListener("change", async () => {
    const file = input.files[0];
    if (!file) return;
    if (!confirm(t("prog.backup.confirm"))) { input.value = ""; return; }
    try {
      const n = Review.importAll(JSON.parse(await file.text()));
      msg.textContent = t("prog.backup.loaded", { n });
      setTimeout(route, 800);
    } catch {
      msg.textContent = t("prog.backup.bad");
    }
    input.value = "";
  });
  return section(null, t("prog.backup.title"),
    h("p", { class: "muted" }, t("prog.backup.why")),
    h("div", { class: "btn-row" },
      h("button", { class: "btn", type: "button", onclick: save }, t("prog.backup.save")),
      h("button", { class: "btn", type: "button", onclick: () => input.click() }, t("prog.backup.load"))),
    input, msg);
}

/* ---------- 주소에 따라 화면 고르기 (해시 라우팅) ---------- */
// #/             → 목록
// #/term/webhook → 용어 카드
// #/about        → 정보
function route() {
  // 이전 화면 정리: 읽던 것 멈추기, 버튼 다시 그리기 함수 지우기, 다음 카드 타이머 끄기
  speech.stop();
  speech.listeners.clear();
  speech.onSentence = null;
  clearTimeout(state.nextTimer);
  state.nextTimer = null;
  clearInterval(state.speakTimer);
  document.body.classList.remove("has-bottom-bar", "no-footer");

  const hash = location.hash || "#/";
  if (hash.startsWith("#/term/")) {
    renderTerm(decodeURIComponent(hash.slice("#/term/".length)));
  } else {
    state.hold = false;
    keepScreenOn(false);
    clearMediaSession();
    if (hash === "#/about") renderAbout();
    else if (hash === "#/study") renderStudy();
    else if (hash === "#/progress") renderProgress();
    else if (hash.startsWith("#/feedback")) renderFeedback(decodeURIComponent(hash.slice("#/feedback/".length)));
    else renderList();
  }
}

/* ---------- 앱 안 브라우저 안내 ---------- */
// 카카오톡·인스타그램 같은 앱 안에서 링크를 열면 그 앱의 작은 브라우저가 열린다.
// 이 브라우저는 음성·화면 켜 두기·잠금 화면 조작이 막혀 있는 경우가 많아 "이동 중" 모드가 안 된다. (2026-11-11 신고)
// → 맨 위에 안내를 띄우고, 카카오톡이면 버튼 하나로 기본 브라우저(크롬·사파리)에서 다시 연다.
function inAppNotice() {
  const ua = navigator.userAgent;
  const kakao = /KAKAOTALK/i.test(ua);
  const other = /NAVER\(inapp|Instagram|FBAN|FBAV|Line\/|DaumApps|everytimeApp|; wv\)/i.test(ua);
  if (!kakao && !other) return;
  const box = h("div", { class: "inapp-notice", role: "status" },
    h("p", {}, kakao ? t("inapp.kakao") : t("inapp.other")),
    kakao && h("a", { class: "btn small primary",
      href: "kakaotalk://web/openExternal?url=" + encodeURIComponent(location.href) }, t("inapp.open"))
  );
  document.querySelector(".wrap").prepend(box);
}

/* ---------- 시작 ---------- */
loadData()
  .then(() => {
    inAppNotice();
    window.addEventListener("hashchange", route);
    route();
  })
  .catch((err) => {
    console.error(err);
    app.replaceChildren(h("p", {}, state.text["error.load"] || "데이터를 불러오지 못했어요. 잠시 뒤 새로고침해 주세요."));
  });
