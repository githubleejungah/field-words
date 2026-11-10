# glossary.json 데이터 모델

- 작성일: 2026-11-10
- 규칙 파일: `schema/glossary.schema.json` (JSON Schema: JSON의 모양을 검사하는 규칙 문서)
- 실제 데이터: `site/data/glossary.json`
- 검사 도구: `python pipeline/validate.py`

## 한눈에 보기

```
glossary.json
├── schema_version   "1.0"         ← 구조 버전
├── updated_at       "2026-11-10"
├── terms[]                        ← 용어 카드 목록
│   ├── id           "webhook"     ← 바꾸지 않는 이름표 (슬러그)
│   ├── term_en / term_ko / aliases[] / expansion?
│   ├── pronunciation { ko, read_as, tts?, variants?, note? }   ← 필수
│   ├── stage (9단계) / also_stages[]? / level (1~4)          ← 필수
│   ├── definition / analogy? / pitfall? / interview_q? / interview_a?
│   ├── prerequisites[]?                                     ← 선수 지식
│   ├── replaced_by?                                         ← 합치거나 이름 바꿀 때
│   ├── examples[]   { context: meeting|interview|review, sentence }
│   ├── tags[] / related[]
│   ├── sources[]    { type, label, url?, date }
│   ├── visual?      { kind, format, file, alt }      ← 있을 때만
│   ├── learn_more?  [{ title, url, kind }]           ← 있을 때만
│   └── created_at / updated_at
└── confusable_pairs[]             ← 혼동 쌍 목록
    └── { id, a, b, difference, visual?, check }
```

`?`가 붙은 칸은 **선택 칸(Optional Field)**입니다. 없으면 칸 자체를 생략합니다.

## 설계 결정 7가지

| # | 결정 | 이유 |
|---|---|---|
| 1 | `id`는 영어 소문자 **슬러그(Slug: 주소에 쓰기 좋은 짧은 이름)** | 복습 기록이 localStorage에 `id`로 저장된다. 바뀌면 수강생 기록이 끊긴다 |
| 2 | 예문 상황은 `meeting / interview / review` 세 값만 허용 | **열거형(Enum: 정해진 값 중 하나만 고르게 하는 규칙)**. "회의", "업무회의"처럼 표기가 흩어지는 것을 막는다. 화면에 보이는 한국어 이름은 사이트가 정한다 |
| 3 | 혼동 쌍은 `confusable_pairs`에 **한 번만** 적는다 | 웹훅 카드와 폴링 카드에 각각 적으면 한쪽만 고치는 실수가 생긴다. 한곳에만 두는 원칙을 **단일 진실 공급원(Single Source of Truth)**이라고 한다. 용어별 `confusable_with`는 사이트가 여기서 계산한다 |
| 4 | 혼동 쌍은 `a`(베이지)와 `b`(세이지)로 나눈다 | 데이터는 "어느 쪽인지"만 정한다. 실제 색은 CSS 디자인 토큰이 정한다 (관심사 분리) |
| 5 | `sources`는 배열 | 강의에서 같은 용어가 다시 나오면 새 카드 대신 출처만 추가한다 |
| 6 | 승인 상태(`status`) 칸이 **없다** | 공개 파일에는 승인된 것만 들어간다. 승인 전 후보는 `pipeline/candidates/`에 따로 두고 Git에 올리지 않는다 |
| 7 | 복습 기록과 소리 프리셋 설정은 이 파일에 **없다** | 사람마다 다르다. 각자 브라우저의 localStorage에 둔다 |
| 8 | 발음(`pronunciation`)은 **필수** 칸 | 듣기만 해도 배우는 앱이다. 처음부터 넣어야 80개를 나중에 한꺼번에 채우는 고생이 없다. `ko`는 화면 표시용, `tts`는 영어 음성용 힌트 |

| 9 | `stage`(단계)와 `level`(등급)은 **필수** | 프로젝트 순서대로 배우는 지도, 수준별 시작점, "이미 알아요" 건너뛰기의 바탕이다. 기준은 `docs/콘텐츠_작성_가이드.md` |
| 10 | `pitfall`, `interview_q`, `expansion`은 선택 | 학습자가 가장 많이 묻는 세 가지에 답한다: "현업에서 뭘 조심해?", "면접에서 뭘 물어?", "약어가 뭐의 줄임말이야?" 많이 아는 사람이 지루하지 않게 하는 재료다 |
| 10-1 | `interview_a`(30초 모범 답변)는 선택 | 성공 지표 "무작위 용어 10개 중 8개를 30초 안에 말로 설명"을 그대로 연습하는 면접 연습 모드의 정답지다 |
| 11 | 용어는 **지우지 않는다.** `replaced_by`로 옮긴다 | 지우면 수강생 브라우저의 복습 기록이 갈 곳을 잃는다. 사이트는 대체된 용어를 목록에서 숨기고 기록을 새 용어로 옮긴다 |

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

## 브라우저 저장소(localStorage) 이름 규칙

glossary.json 밖에 있는, 사람마다 다른 데이터입니다. 이름을 미리 정해 두면 나중에 구조를 바꿀 때 옛 기록을 새 구조로 옮길 수 있습니다. 이 작업을 **마이그레이션(Migration)**이라고 합니다.

```
fw:v1:review:<용어 id>     복습 기록   { box, next_review_at, history[], confidence, lapses, long_term_at? }
                                        box: 1~7 = 라이트너 상자(1·2·4·7·15·30·60일), 8 = 🏅 장기 기억 유지(120일마다)
                                        lapses: 높은 상자에서 잊은 횟수 / long_term_at: 처음 장기 기억이 된 날
fw:v1:today                오늘 기록   { date, seen[], wrong[], misconceptions[], corrected[] } ← 오늘의 마무리용
fw:v1:pair:<혼동 쌍 id>     혼동 쌍 퀴즈 기록
fw:v1:settings             프리셋, 하루 목표, 언어
fw:v1:onboarding           첫 실행 설문 결과
fw:v1:streak               연속 학습일
```

- `fw` = Field Words. 같은 주소(GitHub Pages)에 다른 앱이 있어도 이름이 겹치지 않게 한다.
- `v1` = 저장 구조 버전. 구조가 바뀌면 `v2`로 옮기는 코드를 한 번 실행한다.
- 나중에 만들 **기록 내보내기·가져오기**(Should)는 `fw:` 로 시작하는 값을 모두 파일 하나로 묶는다. 휴대폰을 바꾸거나 브라우저 데이터를 지울 때 기록을 지킬 수 있다.

## 버전 규칙

- 칸을 **추가**하면 `1.0 → 1.1`. 옛 사이트도 새 파일을 읽을 수 있다.
- 칸의 뜻을 바꾸거나 **삭제**하면 `1.x → 2.0`. 사이트도 함께 고친다.
- 예정된 추가: 후원 예문 표시(`examples[].sponsor`), 광고 탑재 시점에 1.1로 추가한다.
