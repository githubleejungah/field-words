/* =========================================================
   현장어 v0.1 — 목록 · 검색 · 용어 카드 · 듣기
   프레임워크 없이 브라우저 기본 기능(DOM, fetch, Web Speech API)만 쓴다.
   ========================================================= */

const APP_VERSION = "0.1.0";

// 단계 순서 (프로젝트 지도). 화면의 단계 버튼이 이 순서로 나온다.
const STAGES = ["discovery", "design", "build", "test", "deploy", "operate", "secure", "grow", "automate"];

// 앱이 기억하는 값(상태, State)을 한곳에 모은다.
const state = {
  terms: [],          // 공개 중인 용어 (대체된 용어 제외)
  allById: new Map(), // id → 용어 (대체된 용어 포함. 옛 링크를 새 용어로 보내기 위해)
  pairs: [],          // 혼동 쌍
  text: {},           // 화면 문구 (i18n/ko.json)
  query: "",          // 검색어
  stage: "all",       // 고른 단계
};

const app = document.getElementById("app");

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
  const [glossary, text] = await Promise.all([
    fetch("data/glossary.json").then((r) => r.json()),
    fetch("i18n/ko.json").then((r) => r.json()),
  ]);
  state.text = text;
  state.pairs = glossary.confusable_pairs;
  for (const term of glossary.terms) state.allById.set(term.id, term);
  state.terms = glossary.terms.filter((term) => !term.replaced_by);
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

  // 점수 높은 순 → 같은 점수면 단계 순서 → 영어 이름 순
  results.sort((a, b) =>
    b.score - a.score ||
    STAGES.indexOf(a.term.stage) - STAGES.indexOf(b.term.stage) ||
    a.term.term_en.localeCompare(b.term.term_en)
  );
  return results.map((r) => r.term);
}

/* ---------- 화면 1: 목록 ---------- */

function renderList() {
  const results = h("div");

  // 검색어나 단계를 바꾸면 결과 부분만 다시 그린다. (검색창을 다시 그리면 입력 중이던 글자 포커스가 사라진다)
  function update() {
    const found = searchTerms();
    results.replaceChildren(
      h("div", { class: "list-head" },
        h("p", { class: "muted" }, t("search.count", { n: found.length })),
        // 지금 보이는 용어들(단계·검색 결과)을 차례로 자동으로 듣는다
        found.length > 0 && h("a", { class: "btn primary", href: "#/walk" }, icon("walk"), t("walk.entry"))
      ),
      found.length
        ? h("ul", { class: "list" }, found.map(listItem))
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

  const chips = h("div", { class: "chips", role: "group", "aria-label": "단계" },
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

  app.replaceChildren(firstNotice() ?? "", input, chips, results);
  update();
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

function listItem(term) {
  return h("li", {},
    h("a", { href: `#/term/${term.id}` },
      h("span", { class: "term-en" }, term.term_en),
      h("span", { class: "term-ko" }, term.term_ko),
      h("span", { class: "term-def" }, term.definition)
    )
  );
}

/* ---------- 화면 2: 용어 카드 ---------- */

function renderTerm(id) {
  let term = state.allById.get(id);
  // 이름이 바뀐 용어의 옛 주소로 들어오면 새 용어로 보낸다
  if (term?.replaced_by) { location.replace(`#/term/${term.replaced_by}`); return; }
  if (!term) {
    app.replaceChildren(h("a", { class: "btn", href: "#/" }, t("nav.back")), h("p", {}, t("card.not_found")));
    return;
  }

  const pron = term.pronunciation;
  const card = h("article", { class: "card" },
    h("h1", {}, term.term_en, h("span", { class: "pron" }, `[${pron.ko}]`)),
    term.term_ko !== term.term_en && h("p", { class: "term-ko-big" }, term.term_ko),

    h("div", { class: "badges" },
      h("span", { class: "badge" }, t(`stage.${term.stage}`)),
      h("span", { class: "badge" }, t(`level.${term.level}`)),
      (term.tags ?? []).map((tag) => h("span", { class: "badge" }, `#${tag}`))
    ),

    term.expansion && h("div", { class: "expansion" },
      h("b", {}, term.expansion),
      term.expansion_ko
    ),

    speakButtons(term),
    (pron.note || pron.variants?.length > 0) && h("p", { class: "pron-tip" },
      pron.note && h("span", {}, pron.note),
      pron.variants?.length > 0 && h("span", {}, `${t("card.variants")}: ${pron.variants.join(", ")}`)
    ),

    section(t("card.definition"), h("p", {}, term.definition)),
    term.analogy && section(t("card.analogy"), h("p", {}, term.analogy)),
    section(t("card.examples"), h("ul", { class: "examples" },
      term.examples.map((ex) => h("li", {}, h("span", { class: "ctx" }, t(`context.${ex.context}`)), ex.sentence))
    )),
    term.pitfall && section(t("card.pitfall"), h("p", { class: "pitfall" }, term.pitfall)),
    pairSection(term),
    term.interview_q && section(t("card.interview"),
      h("p", {}, term.interview_q),
      term.interview_a && h("details", { class: "answer" },
        h("summary", {}, t("card.interview.show")),
        h("p", {}, term.interview_a)
      )
    ),
    linkSection(t("card.prerequisites"), term.prerequisites),
    linkSection(t("card.related"), term.related),
    term.also_stages?.length > 0 && section(t("card.also_stages"),
      h("div", { class: "badges" }, term.also_stages.map((s) => h("span", { class: "badge" }, t(`stage.${s}`))))
    ),
    sourceSection(term)
  );

  app.replaceChildren(h("p", {}, h("a", { class: "btn", href: "#/" }, t("nav.back"))), card);
  window.scrollTo(0, 0);
}

function section(title, ...body) {
  return h("section", { class: "section" }, h("h2", {}, title), ...body);
}

// 혼동 쌍은 confusable_pairs 한곳에만 있다. 이 용어가 들어 있는 쌍을 여기서 찾는다 (단일 진실 공급원).
function pairSection(term) {
  const pairs = state.pairs.filter((p) => p.a === term.id || p.b === term.id);
  if (!pairs.length) return null;
  return section(t("card.pair"), pairs.map((p) => {
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
  return section(t("card.sources"), h("div", { class: "links" }, shown.map((s) =>
    s.url ? h("a", { href: s.url, target: "_blank", rel: "noopener" }, s.label) : h("span", {}, s.label)
  )));
}

// 다른 용어로 가는 링크. 아직 없는 용어는 점선 이름표로만 보여 준다.
function linkSection(title, ids) {
  if (!ids?.length) return null;
  return section(title, h("div", { class: "links" }, ids.map((id) => {
    const other = state.allById.get(id);
    return other ? h("a", { href: `#/term/${id}` }, other.term_en) : h("span", {}, id);
  })));
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
  owner: null,         // 지금 재생 중인 버튼: "term"(발음) 또는 "all"(전체)
  status: "idle",      // idle(멈춤) / playing(재생 중) / paused(일시정지)
  queue: [],           // 읽을 문장 목록
  index: 0,            // 지금 읽는 문장 번호
  token: 0,            // 재생을 새로 시작하거나 멈출 때마다 바뀐다. 이전 재생의 남은 문장이 이어지지 않게 한다
  timer: null,
  listeners: new Set(),// 상태가 바뀌면 버튼 모양을 다시 그리는 함수들

  toggle(owner, makeParts) {
    if (this.owner === owner && this.status === "playing") return this.pause();
    if (this.owner === owner && this.status === "paused") return this.run(this.index);
    this.start(owner, makeParts());
  },

  // onFinish: 끝까지 다 읽었을 때 부를 함수 (이동 모드가 다음 카드로 넘어갈 때 쓴다)
  start(owner, parts, onFinish) {
    this.stop();
    this.owner = owner;
    this.onFinish = onFinish;
    this.queue = parts.flatMap((p) =>
      p.pause ? [p] : this.sentences(p.text, p.lang).map((s) => ({ text: s, lang: p.lang }))
    );
    this.run(0);
  },

  // from번째 문장부터 한 문장씩 읽는다. 한 문장이 끝나면(onend) 다음 문장을 읽는다.
  run(from) {
    if (!this.supported) return;
    this.halt();
    const myToken = this.token;
    this.setStatus("playing");

    const next = (i) => {
      if (myToken !== this.token) return;     // 그사이 멈췄거나 다른 재생이 시작됨
      this.index = i;
      if (i >= this.queue.length) {                            // 다 읽음
        const done = this.onFinish;
        this.owner = null;
        this.onFinish = null;
        this.setStatus("idle");
        done?.();
        return;
      }
      const p = this.queue[i];
      if (p.pause) { this.timer = setTimeout(() => next(i + 1), p.pause); return; }

      const u = new SpeechSynthesisUtterance(p.text);
      u.lang = p.lang;
      const voice = this.voiceFor(p.lang);
      if (voice) u.voice = voice;
      u.rate = 0.95;
      u.onend = () => next(i + 1);
      u.onerror = () => next(i + 1);
      speechSynthesis.speak(u);
    };
    next(from);
  },

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
    if (this.supported) speechSynthesis.cancel();
  },

  setStatus(status) {
    this.status = status;
    this.listeners.forEach((fn) => fn());
  },

  // 기호를 정리하고 문장 단위로 나눈다. 긴 문단을 나누는 이유: 일부 브라우저는 15초가 넘는 문장을 중간에 끊는다.
  sentences(text, lang) {
    let s = this.clean(text);
    if (lang.startsWith("ko")) s = koreanCounters(s);
    return s.split(/(?<=[.?!])\s+/).filter(Boolean);
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
function koreanCounters(text) {
  return text.replace(/(\d{1,2})\s?(번|개|명|장|시간|가지|달|군데|살|마리|권)/g,
    (all, num, unit) => {
      const n = Number(num);
      return n >= 1 && n <= 99 ? `${nativeNumber(n)} ${unit}` : all;
    });
}

function speakButtons(term) {
  if (!speech.supported) return h("p", { class: "muted" }, t("speak.unsupported"));
  return h("div", { class: "speak-row" },
    speakButton("term", t("speak.term"), () => termOnlyParts(term)),
    speakButton("all", t("speak.all"), () => fullParts(term))
  );
}

// ----- 읽을 문장 만들기: 카드의 듣기 버튼과 이동 모드가 함께 쓴다 -----

// 영어 음성이 없는 기기도 있다(예: 한국어 음성만 깔린 윈도우).
// 그때 한국어 음성이 영어 철자를 읽으면 어색하므로, 한글 발음 표기를 대신 읽는다.
// 음성 목록은 늦게 준비되는 브라우저가 있어서 읽을 때마다 확인한다.
const hasEnglishVoice = () => Boolean(speech.voiceFor("en-US"));

function termPart(term) {
  return hasEnglishVoice()
    ? { text: term.pronunciation.tts ?? term.term_en, lang: "en-US" }
    : { text: term.pronunciation.ko, lang: "ko-KR" };
}

function termOnlyParts(term) { return [termPart(term)]; }

// 전체 듣기 순서: 화면 위에서 아래로 보이는 순서와 같다.
// 면접 질문 뒤에는 3초 쉬어서, 답을 듣기 전에 먼저 떠올려 보게 한다 (인출 연습).
function fullParts(term) {
  const hasEnglish = hasEnglishVoice();

  // 한국어 문장 속 영어 용어(예: "OAuth로 붙이면", "MVP는")도 영어 음성이 없으면 한글 발음으로 바꿔 읽는다.
  const ko = (text) => ({ text: hasEnglish ? text : toKoreanSounds(text), lang: "ko-KR" });

  // 다른 용어 이름을 한국어 문장 안에서 읽을 때는 한글 발음으로 읽는다. (예: "엠브이피")
  const sayName = (id) => state.allById.get(id)?.pronunciation.ko;

  const pairs = state.pairs.filter((p) => p.a === term.id || p.b === term.id);
  const related = (term.related ?? []).map(sayName).filter(Boolean);

  // 약어 풀이는 화살표 뒤 우리말 부분만 읽는다. ("Proof(증명) of …" 같은 영어 단어를 한국어 음성이 읽으면 어색하다)
  // 예: "Proof(증명) of Concept(개념) → 개념 증명. 우리말로는…" → "개념 증명. 우리말로는…"
  const expansionKo = term.expansion_ko?.split("→").pop().trim();

  return [
    termPart(term),
    term.expansion && hasEnglish && { text: term.expansion, lang: "en-US" },
    expansionKo && ko(expansionKo),
    ko(`${t("speak.def_prefix")} ${term.definition}`),
    term.analogy && ko(`${t("speak.analogy_prefix")} ${term.analogy}`),
    ...term.examples.map((ex) => ko(`${t(`context.${ex.context}`)}. ${ex.sentence}`)),
    term.pitfall && ko(`${t("card.pitfall")}. ${term.pitfall}`),
    ...pairs.map((p) => {
      const otherId = p.a === term.id ? p.b : p.a;
      return ko(`${t("card.pair")}은 ${sayName(otherId)}. ${t("card.pair.diff")}. ${p.difference}`);
    }),
    term.interview_q && ko(`${t("card.interview")}. ${term.interview_q}`),
    term.interview_q && term.interview_a && { pause: 3000 },
    term.interview_a && ko(`${t("speak.answer_prefix")}. ${term.interview_a}`),
    related.length > 0 && ko(`${t("card.related")}. ${related.join(", ")}.`),
  ].filter(Boolean);
}

// 듣기 버튼 하나 = 재생 ↔ 일시정지 토글.
//   멈춤 상태:    🔈 + 원래 이름("전체 듣기"), 연한 버튼
//   재생 중:      ⏸ + "일시정지", 진한 버튼  → 누르면 일시정지
//   일시정지 상태: ▶ + "이어 듣기", 진한 테두리 → 누르면 멈춘 문장부터 이어서
// 아이콘은 "지금 누르면 일어날 일"을 보여 준다. 음악 앱·유튜브와 같은 약속이다.
function speakButton(key, label, makeParts) {
  const btn = h("button", { class: "btn speak-btn", type: "button", onclick: () => speech.toggle(key, makeParts) });
  const render = () => {
    const mine = speech.owner === key;
    const playing = mine && speech.status === "playing";
    const paused = mine && speech.status === "paused";
    btn.classList.toggle("playing", playing);
    btn.classList.toggle("paused", paused);
    btn.setAttribute("aria-pressed", String(playing));
    btn.replaceChildren(
      icon(playing ? "pause" : paused ? "play" : "speaker"),
      playing ? t("speak.pause") : paused ? t("speak.resume") : label
    );
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

/* ---------- 화면 4: 이동 모드 ---------- */
// 걸을 때·대중교통에서 화면을 보지 않고 듣기만 하는 모드.
// - 목록 화면에서 고른 단계·검색 결과를 차례로 듣는다.
// - 카드 한 장을 다 읽으면 2초 쉬고 다음 카드로 자동으로 넘어간다 (누르지 않아도 된다).
// - 큰 버튼 3개: 이전 / 재생·일시정지 / 다음
// - 화면 켜 두기(Wake Lock API): 화면이 꺼지면 브라우저가 읽기를 멈추기 때문에, 듣는 동안 화면을 켜 둔다.
// - 잠금 화면·이어폰 버튼(Media Session API): 지원하는 기기에서만 동작한다.
const WALK_GAP_MS = 2000;
const walk = { list: [], i: 0, timer: null, wakeLock: null, active: false, done: false, render: null };

function renderWalk() {
  walk.list = searchTerms();
  walk.i = 0;
  walk.done = false;
  walk.active = true;

  const back = h("p", {}, h("a", { class: "btn", href: "#/" }, t("walk.exit")));
  if (!walk.list.length) { app.replaceChildren(back, h("p", {}, t("walk.empty"))); return; }
  if (!speech.supported) { app.replaceChildren(back, h("p", {}, t("speak.unsupported"))); return; }

  const progress = h("p", { class: "walk-progress" });
  const name = h("h1", { class: "walk-term" });
  const sub = h("p", { class: "walk-sub" });
  const def = h("p", { class: "walk-def" });
  const prevBtn = h("button", { class: "walk-btn", type: "button", "aria-label": t("walk.prev"), onclick: () => walkGo(walk.i - 1) }, icon("prev"));
  const playBtn = h("button", { class: "walk-btn main", type: "button", onclick: walkToggle });
  const nextBtn = h("button", { class: "walk-btn", type: "button", "aria-label": t("walk.next"), onclick: () => walkGo(walk.i + 1) }, icon("next"));
  const note = h("p", { class: "muted walk-note" }, "wakeLock" in navigator ? t("walk.wake.on") : t("walk.wake.off"));

  // 상태가 바뀔 때마다 화면을 다시 그린다 (speech.listeners에 등록)
  walk.render = () => {
    const term = walk.list[walk.i];
    const playing = walkIsPlaying();
    const paused = speech.owner === "walk" && speech.status === "paused";
    progress.textContent = `${walk.i + 1} / ${walk.list.length} · ${t(`stage.${term.stage}`)}`;
    name.replaceChildren(term.term_en, h("span", { class: "pron" }, ` [${term.pronunciation.ko}]`));
    sub.textContent = term.term_ko;
    def.textContent = term.definition;
    playBtn.classList.toggle("playing", playing);
    playBtn.setAttribute("aria-pressed", String(playing));
    playBtn.replaceChildren(
      icon(playing ? "pause" : "play"),
      h("span", {}, playing ? t("speak.pause") : paused ? t("speak.resume") : walk.done ? t("walk.again") : t("walk.start"))
    );
    prevBtn.disabled = walk.i === 0;
    nextBtn.disabled = walk.i >= walk.list.length - 1;
    updateMediaSession(term);
  };
  speech.listeners.add(walk.render);

  app.replaceChildren(back, h("section", { class: "walk" },
    progress, name, sub, def,
    h("div", { class: "walk-controls" }, prevBtn, playBtn, nextBtn),
    note
  ));
  walk.render();
}

// 읽는 중이거나, 다음 카드로 넘어가기 전 2초 쉬는 중이면 "재생 중"으로 본다
function walkIsPlaying() {
  return (speech.owner === "walk" && speech.status === "playing") || walk.timer !== null;
}

// 지금 카드를 처음부터 읽고, 다 읽으면 2초 뒤 다음 카드로 넘어간다
function walkPlayCurrent() {
  clearTimeout(walk.timer);
  walk.timer = null;
  walk.done = false;
  keepScreenOn(true);
  speech.start("walk", fullParts(walk.list[walk.i]), () => {
    if (walk.i >= walk.list.length - 1) {   // 마지막 카드까지 다 들음
      walk.done = true;
      keepScreenOn(false);
      walk.render();
      return;
    }
    walk.timer = setTimeout(() => { walk.timer = null; walk.i += 1; walkPlayCurrent(); }, WALK_GAP_MS);
    walk.render();
  });
}

function walkToggle() {
  if (walk.timer !== null) {                 // 2초 쉬는 중에 누르면: 다음 카드에서 멈춰 둔다
    clearTimeout(walk.timer);
    walk.timer = null;
    walk.i = Math.min(walk.i + 1, walk.list.length - 1);
    keepScreenOn(false);
    walk.render();
    return;
  }
  if (speech.owner === "walk" && speech.status === "playing") { speech.pause(); keepScreenOn(false); return; }
  if (speech.owner === "walk" && speech.status === "paused") { keepScreenOn(true); speech.run(speech.index); return; }
  if (walk.done) walk.i = 0;                 // 다 들은 뒤에는 처음부터
  walkPlayCurrent();
}

// 이전·다음 카드로. 듣는 중이었으면 새 카드를 바로 읽고, 멈춰 있었으면 화면만 바꾼다.
function walkGo(i) {
  if (i < 0 || i >= walk.list.length) return;
  const wasPlaying = walkIsPlaying();
  clearTimeout(walk.timer);
  walk.timer = null;
  walk.done = false;
  walk.i = i;
  speech.stop();
  if (wasPlaying) walkPlayCurrent(); else walk.render();
}

function exitWalk() {
  if (!walk.active) return;
  walk.active = false;
  clearTimeout(walk.timer);
  walk.timer = null;
  keepScreenOn(false);
  clearMediaSession();
}

// 화면 켜 두기. 배터리 절약 모드 등에서는 거절될 수 있어서 실패해도 조용히 넘어간다.
async function keepScreenOn(on) {
  if (!("wakeLock" in navigator)) return;
  try {
    if (on && !walk.wakeLock) {
      walk.wakeLock = await navigator.wakeLock.request("screen");
      walk.wakeLock.addEventListener("release", () => { walk.wakeLock = null; });
    } else if (!on && walk.wakeLock) {
      await walk.wakeLock.release();
      walk.wakeLock = null;
    }
  } catch { /* 무시 */ }
}
// 다른 앱에 갔다 돌아오면 화면 켜 두기가 풀려 있으므로 다시 건다
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible" && walk.active && walkIsPlaying()) keepScreenOn(true);
});

// 잠금 화면·이어폰 버튼 연결 (지원하는 기기에서만)
const MEDIA_ACTIONS = ["play", "pause", "nexttrack", "previoustrack"];
function updateMediaSession(term) {
  if (!("mediaSession" in navigator)) return;
  try {
    navigator.mediaSession.metadata = new MediaMetadata({
      title: `${term.term_en} · ${term.term_ko}`,
      artist: t("app.name"),
      album: t(`stage.${term.stage}`),
    });
    navigator.mediaSession.setActionHandler("play", walkToggle);
    navigator.mediaSession.setActionHandler("pause", walkToggle);
    navigator.mediaSession.setActionHandler("nexttrack", () => walkGo(walk.i + 1));
    navigator.mediaSession.setActionHandler("previoustrack", () => walkGo(walk.i - 1));
  } catch { /* 일부 동작을 지원하지 않는 브라우저 */ }
}
function clearMediaSession() {
  if (!("mediaSession" in navigator)) return;
  navigator.mediaSession.metadata = null;
  for (const a of MEDIA_ACTIONS) { try { navigator.mediaSession.setActionHandler(a, null); } catch { /* 무시 */ } }
}

/* ---------- 화면 3: 정보 ---------- */

function renderAbout() {
  app.replaceChildren(
    h("p", {}, h("a", { class: "btn", href: "#/" }, t("nav.back"))),
    h("article", { class: "card" },
      h("h1", {}, t("about.title")),
      section(t("about.data.title"),
        h("div", { class: "notice" },
          h("p", {}, t("about.data.body1")),
          h("p", {}, t("about.data.body2")),
          h("p", {}, t("about.data.body3"))
        )
      ),
      // 피드백 창구가 정해지면 여기를 링크로 바꾼다 (docs/공개_체크리스트.md)
      section(t("about.feedback"), h("p", { class: "muted" }, t("about.feedback.pending"))),
      section(t("about.oss.title"), h("p", {}, t("about.oss.body"))),
      section(t("about.voice"), voiceInfo()),
      section(t("about.version"), h("p", { class: "muted" }, `v${APP_VERSION} · ${state.terms.length}개 용어`))
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
      h("span", {}, `${t("about.voice.en")}: ${en ? en.name : t("about.voice.none")}`)
    );
  };
  fill();
  if (speech.supported) speechSynthesis.addEventListener("voiceschanged", fill, { once: true });
  return box;
}

/* ---------- 주소에 따라 화면 고르기 (해시 라우팅) ---------- */
// #/            → 목록
// #/term/webhook → 용어 카드
// #/about       → 정보
function route() {
  exitWalk();                // 이동 모드에서 나가면 화면 켜 두기·잠금 화면 연결을 푼다
  speech.stop();             // 화면을 옮기면 읽던 것을 멈춘다
  speech.listeners.clear();  // 이전 화면의 버튼은 더 이상 다시 그리지 않는다
  const hash = location.hash || "#/";
  if (hash.startsWith("#/term/")) renderTerm(decodeURIComponent(hash.slice("#/term/".length)));
  else if (hash === "#/walk") renderWalk();
  else if (hash === "#/about") renderAbout();
  else renderList();
}

/* ---------- 시작 ---------- */
loadData()
  .then(() => {
    window.addEventListener("hashchange", route);
    route();
  })
  .catch((err) => {
    console.error(err);
    app.replaceChildren(h("p", {}, "데이터를 불러오지 못했어요. 잠시 뒤 새로고침해 주세요."));
  });
