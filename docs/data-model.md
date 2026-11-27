# glossary.json 데이터 모델

- 작성일: 2026-11-10
- 고친 날: 2026-11-16 — 예문 상황에 `field`(현장에선) 추가, 스키마 1.1 ([ADR-0005](adr/0005-예문-상황에-현장에선-추가.md))
- 고친 날: 2026-11-24 — AI 답 검수 문제 `ai_checks[]` 추가, 스키마 1.2 (요구: [requirements.md](requirements.md), 설계 결정 D-1~D-6 사용자 승인)
- 규칙 파일: `schema/glossary.schema.json` (JSON Schema: JSON의 모양을 검사하는 규칙 문서)
- 실제 데이터: `site/data/glossary.json`
- 검사 도구: `python pipeline/validate.py`

## 한눈에 보기

```
glossary.json
├── schema_version   "1.2"         ← 구조 버전
├── updated_at       "2026-11-10"
├── terms[]                        ← 용어 카드 목록
│   ├── id           "webhook"     ← 바꾸지 않는 이름표 (슬러그)
│   ├── term_en / term_ko / aliases[] / expansion?
│   ├── pronunciation { ko, read_as, ipa?, tts?, variants?, note? }   ← 필수 (ipa: 발음 기호, 2026-11-12)
│   ├── stage (9단계) / also_stages[]? / level (1~4)          ← 필수
│   ├── definition / analogy? / pitfall? / interview_q? / interview_a?
│   ├── prerequisites[]?                                     ← 선수 지식
│   ├── replaced_by?                                         ← 합치거나 이름 바꿀 때
│   ├── examples[]   { context: meeting|interview|review|field, sentence }
│   ├── tags[] / related[]
│   ├── sources[]    { type, label, url?, date }
│   ├── visual?      { kind, format, file, alt }      ← 있을 때만
│   ├── learn_more?  [{ title, url, kind }]           ← 있을 때만
│   └── created_at / updated_at
├── confusable_pairs[]             ← 혼동 쌍 목록
│   └── { id, a, b, difference, visual?, check }
└── ai_checks[]                    ← AI 답 검수 문제 (2026-11-24, 스키마 1.2)
    ├── id            "rate-limit-per-second"   ← 슬러그, 바꾸지 않는다
    ├── type          number | recency | fact | code   ← 숫자 · 최신 정보 · 출처/사실 · 코드
    ├── prompt        사용자가 AI에게 한 질문
    ├── statements[]  AI 답 문장 정확히 3개
    ├── wrong         0 | 1 | 2   ← 틀린 문장 번호 = 정답
    ├── correction    바른 내용 1줄
    ├── how_to_check  확인 방법 1줄
    ├── calc?         계산식 (type = number 이면 필수)
    ├── sources[]     { label, url, checked_at } 1개 이상 (공식 문서 · 명세 · MDN 등)
    ├── checked_at    사람이 공식 출처로 확인한 날
    ├── recheck_at    다시 확인할 날 ← 파이프라인이 계산 (최신 정보 +6개월, 나머지 +1년)
    ├── terms[]       관련 용어 id 1개 이상
    ├── retired_at?   내린 날 (있으면 사이트가 목록 · 링크에서 뺀다)
    └── created_at / updated_at
```

`?`가 붙은 칸은 **선택 칸(Optional Field)**입니다. 없으면 칸 자체를 생략합니다.

## 데이터 소유와 정본

**정본(正本, Source of Truth)**은 "값이 둘로 갈라지면 이쪽이 맞다"고 정한 원본입니다. **주인(Owner)**은 정본을 바꿀 수 있는 사람·프로그램입니다. **사본(Copy)**은 정본에서 만들어진 것이라, 고칠 때는 사본이 아니라 정본을 고칩니다.

| 데이터 | 정본 (어디에) | 주인 (누가 바꾸나) | 사본 · 파생 |
|---|---|---|---|
| 공개 용어 · 혼동 쌍 | `site/data/glossary.json` (Git) | 관리자. 사람이 승인한 뒤 `seedlib.py`·`promote.py`·`seeds/update_*.py`로 쓴다 | 배포된 GitHub Pages의 같은 파일, 브라우저 HTTP 캐시(`no-cache`로 매번 확인), `app.js`의 `state.terms`·`state.allById`(메모리) |
| 용어별 `confusable_with` | 없음 (파생값) | — | `confusable_pairs`에서 사이트가 계산한다. 데이터에 적지 않는다 |
| glossary.json 모양 규칙 | `schema/glossary.schema.json` | 관리자 | 이 문서의 "한눈에 보기"(설명용). 참조 검사는 `validate.py` 코드에 있다 |
| 넣은 용어 묶음의 기록 | `pipeline/seeds/*.py` (Git) | 관리자 (`promote.py`가 후보를 이리로 옮김) | — . 넣은 뒤 내용은 glossary.json이 정본이다. 이 파일을 다시 실행해 되돌리지 않는다 |
| 용어 후보 줄(다듬기 전) | `pipeline/candidates/*_용어후보.md` (**Git 밖**, 관리자 PC). 한 곳에만 둔다(ADR-0007) | 어느 세션이든 중복 확인 뒤 세션마다 새 파일 1개 | `pipeline/candidates/00_후보_목록.md`(개수 · 상태 한 장 목록). 옛 `field-words-inbox` 이슈 1~5번은 닫힌 기록 |
| 승인 전 후보 | `pipeline/candidates/*.py` (**Git 밖**, 관리자 PC) | 주간 예약 작업·Claude가 쓰고 사람이 승인 | `*_미리보기.md`(`preview.py`), `--dry-run` 때의 임시 복사본 |
| 점검 · 제안 보고서 | `pipeline/reports/` (**Git 밖**) | `check_all.py`, 주간 예약 작업 | — |
| 화면 문구 | `site/i18n/ko.json` | 개발자 | `state.text`(메모리) |
| 혼동 쌍 색 · 디자인 토큰 | `site/css/style.css` | 개발자 | — . 데이터에는 넣지 않는다 (ADR-0002) |
| 수강생 학습 기록 | 각 브라우저의 `localStorage` (`fw:v1:*`) | 수강생 본인. 코드에서는 `review.js`만 쓴다 (예외: `notice_seen`은 `app.js`) | 백업 파일 `fieldwords-backup-날짜.json`(수강생이 저장). `localStorage`를 못 쓰면 메모리에만 둔다. 기기 사이 동기화는 없다 |
| 수강생 의견 | 받는 메일함 (주소는 `app.js`의 `FEEDBACK.mailto`) | 프로젝트 오너 | 보낸 사람 메일 앱의 보낸 편지함 |
| API 키 · 비밀 값 | `.env` (**Git 밖**) | 관리자 | 없음. 공개 사이트에 넣지 않는다. 지금 파이프라인 코드는 `.env`를 읽지 않는다 |
| AI 답 검수 문제 | `site/data/glossary.json`의 `ai_checks[]` | 관리자. 사람 승인 뒤 `promote.py`가 넣고, `recheck.py`가 확인일 · 내린 날을 고친다 | 배포된 파일, `app.js`의 `state.checks`(메모리) |
| 다시 확인할 날 `recheck_at` | 같은 곳 (계산값이지만 저장) | 파이프라인만 쓴다(`promote.py` · `recheck.py`). 사람이 손으로 쓰지 않는다 | 주간 점검 보고서의 "다시 확인할 문제" 목록 |
| AI 답 검수 학습 기록 | 각 브라우저 `fw:v1:aic:<문제 id>` | 수강생 본인. 코드에서는 `review.js`만 쓴다 | 기록 백업 파일(`fw:` 묶음에 자동 포함) |
| 게임 코드 · 게임 데이터(문제 · 파이썬 연습 등) | 게임 저장소 `field-words-3d-lab`의 `main` (**이 저장소 밖**) | 게임 개발 세션(사람 승인 뒤 커밋). 필드워드 쪽에서는 고치지 않는다 | 배포 묶음의 `game/` 폴더(배포할 때마다 새로 받음, ADR-0006). 필드워드 저장소에는 사본을 커밋하지 않는다(AC-105) |
| 게임 학습 기록 | 각 브라우저 `localStorage`의 `cm:v1:*` | 수강생 본인. 코드에서는 게임만 쓴다. 필드워드는 읽지도 쓰지도 않는다 | 없음. 필드워드 기록 백업(`fw:` 묶음)에는 들어가지 않는다. 합칠 때 옮기거나 지우지 않는다(AC-108) |
| 쫑긋과 서로 반영할 목록 | 공유 저장소 `learning-apps-shared/서로_반영할_것.md` (이 저장소 밖) | 사람과 함께하는 작업 | 주간 작업은 읽기만 한다 (`docs/운영_자동화.md`) |

- 서버가 없으므로 수강생 데이터의 정본은 **수강생 기기에만** 있다. 그래서 관리자는 누가 무엇을 틀리는지 모른다. 이 한계를 공개 전에 안내한다(`docs/공개_체크리스트.md`).

## 설계 결정

| # | 결정 | 이유 |
|---|---|---|
| 1 | `id`는 영어 소문자 **슬러그(Slug: 주소에 쓰기 좋은 짧은 이름)** | 복습 기록이 localStorage에 `id`로 저장된다. 바뀌면 수강생 기록이 끊긴다 |
| 2 | 예문 상황은 `meeting / interview / review / field` 네 값만 허용 | **열거형(Enum: 정해진 값 중 하나만 고르게 하는 규칙)**. "회의", "업무회의"처럼 표기가 흩어지는 것을 막는다. 화면에 보이는 한국어 이름은 사이트가 정한다(`i18n/ko.json`의 `context.*`) |
| 2-1 | `field`(화면 이름 "현장에선")는 **실제 겪은 상황 한 줄**만 쓴다 | 회의·면접·리뷰 예문은 "이렇게 말한다"는 연습용이라 꾸며 쓴다. 현장 예시는 실습·작업에서 그 용어를 실제로 만난 장면이라 꾸며 쓰지 않는다. 2026-11-16 추가 ([ADR-0005](adr/0005-예문-상황에-현장에선-추가.md)) |
| 3 | 혼동 쌍은 `confusable_pairs`에 **한 번만** 적는다 | 웹훅 카드와 폴링 카드에 각각 적으면 한쪽만 고치는 실수가 생긴다. 한곳에만 두는 원칙을 **단일 진실 공급원(Single Source of Truth)**이라고 한다. 용어별 `confusable_with`는 사이트가 여기서 계산한다 |
| 4 | 혼동 쌍은 `a`(베이지)와 `b`(세이지)로 나눈다 | 데이터는 "어느 쪽인지"만 정한다. 실제 색은 CSS 디자인 토큰이 정한다 (관심사 분리) |
| 5 | `sources`는 배열 | 강의에서 같은 용어가 다시 나오면 새 카드 대신 출처만 추가한다 |
| 6 | 승인 상태(`status`) 칸이 **없다** | 공개 파일에는 승인된 것만 들어간다. 승인 전 후보는 `pipeline/candidates/`에 따로 두고 Git에 올리지 않는다 |
| 7 | 복습 기록과 소리 프리셋 설정은 이 파일에 **없다** | 사람마다 다르다. 각자 브라우저의 localStorage에 둔다 |
| 8 | 발음(`pronunciation`)은 **필수** 칸 | 듣기만 해도 배우는 앱이다. 처음부터 넣어야 80개를 나중에 한꺼번에 채우는 고생이 없다. `ko`는 한국 현업 발음(화면에 "현업 발음"으로 표시), `ipa`는 미국 영어 발음 기호(단어 아래에 /…/로 표시), `tts`는 영어 음성용 힌트 |
| 9 | `stage`(단계)와 `level`(등급)은 **필수** | 프로젝트 순서대로 배우는 지도, 수준별 시작점, "이미 알아요" 건너뛰기의 바탕이다. 기준은 `docs/콘텐츠_작성_가이드.md` |
| 10 | `pitfall`, `interview_q`, `expansion`은 선택 | 학습자가 가장 많이 묻는 세 가지에 답한다: "현업에서 뭘 조심해?", "면접에서 뭘 물어?", "약어가 뭐의 줄임말이야?" 많이 아는 사람이 지루하지 않게 하는 재료다 |
| 10-1 | `interview_a`(30초 모범 답변)는 선택 | 성공 지표 "무작위 용어 10개 중 8개를 30초 안에 말로 설명"을 그대로 연습하는 면접 연습 모드의 정답지다 |
| 12 | AI 답 검수 문제는 **glossary.json 안** `ai_checks[]`에 둔다 (D-1) | "파이프라인과 사이트를 잇는 것은 glossary.json 하나뿐"(CLAUDE.md 확정 결정)을 지킨다. 새 파일을 만들면 이 결정을 바꾸는 ADR이 필요하다 |
| 13 | AI 답 검수 기록은 용어 기록과 **다른 이름** `fw:v1:aic:` (D-4) | 섞이면 "오늘 n / 10장"과 내 기록의 "본 용어" 숫자가 틀어진다. 상태 분류 · 상자 간격은 용어와 같은 규칙을 쓴다(D-3) |
| 14 | 문제는 **지우지 않고** `retired_at`으로 내린다 (D-6) | 용어의 `replaced_by`와 같은 원칙. 지우면 수강생 기록이 갈 곳을 잃는다 |
| 15 | 승인 상태 칸이 **없다** (문제도 같음) | 파일에는 승인된 문제만 들어간다. 후보는 `pipeline/candidates/`(Git 밖) |
| 11 | 용어는 **지우지 않는다.** `replaced_by`로 옮긴다 | 지우면 수강생 브라우저의 복습 기록이 갈 곳을 잃는다. 사이트는 대체된 용어를 목록에서 숨기고 옛 주소를 새 용어로 보낸다. **확인 필요**: 복습 기록을 새 용어로 옮기는 코드는 아직 없다(2026-11-16 main 기준. 지금 `replaced_by`를 쓴 용어도 없다) |

## 스키마가 못 잡는 것 → 검사 스크립트가 잡는다

JSON Schema는 **모양**만 검사합니다. "webhook이라는 id가 실제로 있는가?" 같은 **참조 무결성(Referential Integrity: 가리키는 대상이 실제로 있는지)**은 검사하지 못합니다. 그래서 `pipeline/validate.py`가 한 번 더 봅니다.

| 검사 | 결과 |
|---|---|
| `id` 중복 | 오류 |
| 혼동 쌍의 `a`, `b`가 실제 용어인가 | 오류 |
| 같은 카드에 같은 상황 예문이 두 번 | 오류 |
| `related`·`prerequisites`가 아직 없는 용어를 가리킴 | 경고 (시드가 늘면 생길 용어일 수 있음) |
| `related`·`prerequisites`가 자기 자신을 가리킴 | 오류 |
| `replaced_by`가 없는 용어나 자기 자신을 가리킴 | 오류 (복습 기록이 갈 곳이 없어짐) |
| `also_stages`에 주 단계가 또 있음 | 오류 |
| 혼동 쌍이 대체된 용어를 씀 | 경고 |
| `visual.file` 그림 파일이 아직 없음 | 경고 (Mermaid → SVG 변환 전일 수 있음) |
| AI 답 검수: `id` 중복 · `terms`가 없는 용어 · 공식 출처 url이나 `checked_at` 없음 · 숫자 유형에 `calc` 없음 | 오류 (후보는 미리보기 · 승인 대기열에 올리지 않는다: AC-10 · AC-11) |
| AI 답 검수: `recheck_at`이 유형 규칙(최신 정보 +6개월, 나머지 +1년)과 다름 | 오류 |
| AI 답 검수: `recheck_at`이 지남 | 정보 (주간 점검 보고서에 목록: AC-14) |

## 브라우저 저장소(localStorage) 이름 규칙

glossary.json 밖에 있는, 사람마다 다른 데이터입니다. 이름을 미리 정해 두면 나중에 구조를 바꿀 때 옛 기록을 새 구조로 옮길 수 있습니다. 이 작업을 **마이그레이션(Migration)**이라고 합니다.

```
fw:v1:review:<용어 id>     복습 기록   { box, status, first_at, last_at, next_review_at, history[최근 20개], lapses, long_term_at? }
                                        box: 1~7 = 라이트너 상자(1·2·4·7·15·30·60일), 8 = 🏅 장기 기억 유지(120일마다)
                                        lapses: 높은 상자에서 잊은 횟수 / long_term_at: 처음 장기 기억이 된 날
fw:v1:today                오늘 기록   { date, seen[], wrong[], misconceptions[], corrected[], wrapped[], aic?, aic_kind? } ← aic: 오늘 낸 AI 답 검수 문제 id (하루 1개), aic_kind: new | review
fw:v1:log                  날짜별 학습 일지 { "YYYY-MM-DD": { seen[], new[], wrong[], misconceptions[], corrected[], long_term[] } } ← 내 기록 화면. 지우지 않는다
fw:v1:log_built            일지 되살리기를 마쳤는지 (true)
fw:v1:aic:<문제 id>        AI 답 검수 기록 { box, status, first_at, last_at, next_review_at, history[최근 20개] } ← 용어 기록과 같은 모양
                           일지(fw:v1:log)에는 날짜마다 aic[] · aic_misconceptions[] 칸이 더해진다
fw:v1:settings             설정 { daily_goal(하루 목표, 기본 10), min_goal(기본 3), hl(강조 표시 모양) }
fw:v1:notice_seen          첫 안내를 봤는지 ("1"). 이것만 app.js가 직접 쓴다

예정 (코드에 아직 없음, 2026-11-16 main 기준)
fw:v1:pair:<혼동 쌍 id>     혼동 쌍 퀴즈 기록
fw:v1:onboarding           첫 실행 설문 결과
(프리셋, 언어)              settings에 넣을 예정
```

- 연속 학습일은 저장하지 않는다. `fw:v1:log`에서 매번 계산한다(`Review.stats`).

- `fw` = Field Words. 같은 주소(GitHub Pages)에 다른 앱이 있어도 이름이 겹치지 않게 한다.
- 같은 출처(`https://githubleejungah.github.io`)에 게임 기록 `cm:v1:*`(코드 가려 보기)도 있다. 게임이 `/game/`으로 합쳐져도 출처가 같아 그대로 이어진다. 필드워드는 `fw:`만 다룬다.
- `v1` = 저장 구조 버전. 구조가 바뀌면 `v2`로 옮기는 코드를 한 번 실행한다.
- **기록 내보내기·가져오기**(`Review.exportAll`·`importAll`, 내 기록 화면)는 `fw:` 로 시작하는 값을 모두 파일 하나로 묶는다. 휴대폰을 바꾸거나 브라우저 데이터를 지울 때 기록을 지킬 수 있다. 파일 모양: `{ app: "field-words", format: 1, exported_at, data: { "fw:v1:…": "문자열 값" } }`

## 버전 규칙

- 칸을 **추가**하면 `1.0 → 1.1`. 옛 사이트도 새 파일을 읽을 수 있다.
- 열거형에 **값을 추가**하는 것도 같은 급(1.x 올림)으로 본다. 2026-11-16 예문 상황 `field` 추가로 `1.1`이 됐다.
- 2026-11-24 `ai_checks[]` 목록 추가로 `1.2`가 됐다.
- 칸의 뜻을 바꾸거나 **삭제**하면 `1.x → 2.0`. 사이트도 함께 고친다.
- 예정된 추가: 후원 예문 표시(`examples[].sponsor`), 광고 탑재 시점에 1.1로 추가한다.
