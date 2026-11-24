"""후보: AI 답 검수 첫 묶음 20개 (유형마다 5개) — 2026-11-24
요구: docs/requirements.md (Q3 20개 · Q4 문장 3개 중 틀린 것 1개 · Q5 공식 출처 + 확인일, 숫자면 계산식)
- 상황은 개발 현장(1-1). AI 답 문장은 새로 썼다(출처 문장 복사 없음).
- 출처 20곳(+Retry-After 1곳)은 2026-11-24에 웹에서 열어 주장과 맞는지 확인했다(Claude). 마지막 확인 · 승인은 사람.
- AWS 백오프 글은 본문을 읽지 못해 쓰지 않고, MDN Retry-After 문제로 바꿨다.

미리보기:  python pipeline/preview.py pipeline/candidates/2026-11-24_aicheck.py
넣기(승인 후):  python pipeline/promote.py pipeline/candidates/2026-11-24_aicheck.py
"""
D = "2026-11-24"
MDN = "https://developer.mozilla.org/en-US/docs/"


def S(label, url):
    return [{"label": label, "url": url, "checked_at": D}]


AI_CHECKS = [
    # ---------------- 숫자 (number) ----------------
    dict(id="rate-limit-per-second", type="number",
         prompt="하루 호출 한도가 1,200,000건이면 초당 몇 건으로 잡아야 하나요?",
         statements=["하루 1,200,000건이면 초당 약 140건이에요.",
                     "한도를 넘으면 서버는 보통 429 상태 코드를 돌려줘요.",
                     "응답에 Retry-After 헤더를 붙여 언제 다시 보내면 되는지 알려 줄 수 있어요."],
         wrong=0, correction="초당 약 14건입니다. 하루는 86,400초라서 140건이면 하루 1,200만 건이 넘습니다.",
         how_to_check="하루 = 86,400초로 단위를 맞춰 직접 나눠 보기",
         calc="1,200,000 ÷ 86,400 ≈ 13.9 → 초당 약 14건",
         sources=S("MDN 429 Too Many Requests", MDN + "Web/HTTP/Reference/Status/429"),
         checked_at=D, terms=["rate-limit", "hallucination"]),

    dict(id="cache-max-age-seconds", type="number",
         prompt="Cache-Control의 max-age로 캐시 시간을 정하는 법을 알려 주세요.",
         statements=["max-age 값의 단위는 초예요.",
                     "max-age=604800이면 7일 동안 새것으로 봐요.",
                     "max-age=600이면 1시간 동안 캐시돼요."],
         wrong=2, correction="max-age=600은 600초, 즉 10분입니다. 1시간은 max-age=3600입니다.",
         how_to_check="max-age는 초 단위이므로 60으로 나눠 분으로 바꿔 보기",
         calc="600 ÷ 60 = 10분 · 3,600 ÷ 60 = 60분(1시간) · 604,800 ÷ 86,400 = 7일",
         sources=S("MDN Cache-Control", MDN + "Web/HTTP/Reference/Headers/Cache-Control"),
         checked_at=D, terms=["cache", "cdn"]),

    dict(id="uptime-yearly-downtime", type="number",
         prompt="가동률 목표별로 1년에 멈춰도 되는 시간을 알려 주세요.",
         statements=["99.99%면 1년에 약 52.56분까지 멈출 수 있어요.",
                     "99.9%면 1년에 약 52분까지 멈출 수 있어요.",
                     "9가 하나 늘 때마다 멈춰도 되는 시간은 10분의 1로 줄어요."],
         wrong=1, correction="99.9%면 1년에 약 525.6분(약 8.76시간)까지 멈출 수 있습니다. 52.56분은 99.99%일 때입니다.",
         how_to_check="1년 525,600분에 (100% − 목표)를 곱해 직접 계산하기",
         calc="525,600분 × 0.1% = 525.6분(약 8.76시간) · 525,600분 × 0.01% = 52.56분",
         sources=S("Google SRE Book · Embracing Risk", "https://sre.google/sre-book/embracing-risk/"),
         checked_at=D, terms=["uptime", "sla", "availability"]),

    dict(id="base64-size-increase", type="number",
         prompt="이미지 1MB를 Base64로 바꿔 JSON에 넣으면 크기가 어떻게 되나요?",
         statements=["Base64는 3바이트를 4글자로 바꿔요.",
                     "1MB 이미지를 Base64로 바꾸면 약 0.75MB로 줄어들어요.",
                     "큰 파일은 Base64로 넣기보다 따로 올리고 주소만 넣는 편이 나아요."],
         wrong=1, correction="Base64는 원래보다 약 3분의 1 커집니다. 1MB는 약 1.33MB가 됩니다.",
         how_to_check="3바이트 → 4글자 비율(4 ÷ 3)을 곱해 보기",
         calc="1MB × 4 ÷ 3 ≈ 1.33MB",
         sources=S("MDN Base64", MDN + "Glossary/Base64"),
         checked_at=D, terms=["json", "api"]),

    dict(id="retry-after-seconds", type="number",
         prompt="429 응답에 Retry-After: 120이 왔어요. 언제 다시 보내면 되나요?",
         statements=["Retry-After: 120이면 120밀리초 뒤에 다시 보내면 돼요.",
                     "Retry-After에는 초 대신 날짜를 적을 수도 있어요.",
                     "429뿐 아니라 503 응답에도 Retry-After가 올 수 있어요."],
         wrong=0, correction="Retry-After의 숫자는 초 단위입니다. 120이면 120초, 즉 2분 뒤입니다.",
         how_to_check="MDN에서 Retry-After의 단위(delay-seconds) 확인하기",
         calc="120초 ÷ 60 = 2분",
         sources=S("MDN Retry-After", MDN + "Web/HTTP/Reference/Headers/Retry-After"),
         checked_at=D, terms=["rate-limit", "retry"]),

    # ---------------- 최신 정보 (recency) ----------------
    dict(id="python2-sunset", type="recency",
         prompt="오래된 Python 2 스크립트를 그대로 운영해도 되나요?",
         statements=["Python 2는 아직 공식 보안 업데이트를 받고 있어요.",
                     "Python 2는 2020년 1월 1일에 지원이 끝났어요.",
                     "새로 만드는 코드는 Python 3로 쓰는 게 맞아요."],
         wrong=0, correction="Python 2는 2020-01-01에 지원이 끝나 더는 보안 업데이트가 나오지 않습니다.",
         how_to_check="python.org의 Python 2 지원 종료 안내에서 날짜 확인하기",
         sources=S("python.org · Sunsetting Python 2", "https://www.python.org/doc/sunset-python-2/"),
         checked_at=D, terms=["technical-debt", "hallucination"]),

    dict(id="python38-eol", type="recency",
         prompt="서버에 Python 3.8이 깔려 있는데 그대로 써도 되나요?",
         statements=["Python 3.8은 2024년 10월에 지원이 끝났어요.",
                     "Python 3.8은 2026년까지 보안 패치를 받아요.",
                     "버전별 지원 종료일은 Python 개발자 안내서의 버전 표에서 볼 수 있어요."],
         wrong=1, correction="Python 3.8은 2024-10-07에 지원이 끝났습니다(end-of-life).",
         how_to_check="devguide.python.org의 버전 표에서 지원 종료일 확인하기",
         sources=S("Python Developer's Guide · Status of Python versions", "https://devguide.python.org/versions/"),
         checked_at=D, terms=["technical-debt"]),

    dict(id="nodejs18-eol", type="recency",
         prompt="새 서비스를 Node.js 18로 시작해도 될까요?",
         statements=["Node.js 18은 2027년까지 LTS로 지원돼요.",
                     "지원이 끝난 버전은 보안 패치가 나오지 않아요.",
                     "Node.js의 버전별 상태는 공식 사이트 이전 릴리스 표에서 볼 수 있어요."],
         wrong=0, correction="Node.js 18은 이미 지원이 끝난(EOL) 버전입니다. 새 서비스는 지원 중인 LTS 버전으로 시작합니다.",
         how_to_check="nodejs.org의 이전 릴리스 표에서 v18 상태 확인하기",
         sources=S("Node.js · Previous Releases", "https://nodejs.org/en/about/previous-releases"),
         checked_at=D, terms=["technical-debt", "library"]),

    dict(id="upload-artifact-v3", type="recency",
         prompt="GitHub Actions에서 actions/upload-artifact@v3를 계속 써도 되나요?",
         statements=["v3는 계속 지원되니 바꿀 필요가 없어요.",
                     "v3는 2025년 1월 30일부터 쓸 수 없게 됐어요.",
                     "v4로 올리고 다운로드 쪽(download-artifact)도 함께 올려야 해요."],
         wrong=0, correction="upload-artifact · download-artifact v3는 2025-01-30부터 쓸 수 없습니다. v4로 올립니다.",
         how_to_check="GitHub 변경 공지(Changelog)에서 v3 종료 안내 확인하기",
         sources=S("GitHub Changelog · Deprecation notice: v3 of the artifact actions",
                   "https://github.blog/changelog/2024-04-16-deprecation-notice-v3-of-the-artifact-actions/"),
         checked_at=D, terms=["ci-cd", "pipeline"]),

    dict(id="tls10-deprecated", type="recency",
         prompt="오래된 장비 때문에 TLS 1.0을 켜 둬도 괜찮을까요?",
         statements=["RFC 8996은 TLS 1.0과 1.1을 공식적으로 쓰지 말라고 정했어요.",
                     "TLS 1.0은 지금도 권장되는 안전한 버전이에요.",
                     "TLS 1.2 이상을 쓰는 것이 맞아요."],
         wrong=1, correction="TLS 1.0과 1.1은 RFC 8996으로 폐기(deprecated)됐습니다. TLS 1.2 이상을 씁니다.",
         how_to_check="IETF RFC 8996 요약(Abstract) 읽기",
         sources=S("IETF RFC 8996 · Deprecating TLS 1.0 and TLS 1.1", "https://datatracker.ietf.org/doc/html/rfc8996"),
         checked_at=D, terms=["defense-in-depth", "zero-trust"]),

    # ---------------- 출처/사실 (fact) ----------------
    dict(id="http-429-meaning", type="fact",
         prompt="API가 429를 돌려줘요. 무슨 뜻인가요?",
         statements=["429는 서버 내부 오류라는 뜻이에요.",
                     "429는 짧은 시간에 요청을 너무 많이 보냈다는 뜻이에요.",
                     "Retry-After 헤더가 있으면 그 시간만큼 기다렸다 다시 보내요."],
         wrong=0, correction="429는 Too Many Requests(요청이 너무 많음)입니다. 서버 내부 오류는 500입니다.",
         how_to_check="MDN HTTP 상태 코드 목록에서 429 찾기",
         sources=S("MDN 429 Too Many Requests", MDN + "Web/HTTP/Reference/Status/429"),
         checked_at=D, terms=["rate-limit", "api"]),

    dict(id="http-401-vs-403", type="fact",
         prompt="로그인 안 한 사용자와 권한 없는 사용자에게 어떤 상태 코드를 줘야 하나요?",
         statements=["403은 로그인하지 않아서 누구인지 모를 때 써요.",
                     "401은 유효한 인증 정보가 없을 때 써요.",
                     "403은 누구인지 알지만 권한이 없을 때 써요. 다시 로그인해도 달라지지 않아요."],
         wrong=0, correction="로그인하지 않아 누구인지 모를 때는 401입니다. 403은 누구인지 알아도 권한이 없을 때입니다.",
         how_to_check="MDN에서 401과 403 설명을 나란히 읽기",
         sources=S("MDN 401 Unauthorized", MDN + "Web/HTTP/Reference/Status/401")
                 + S("MDN 403 Forbidden", MDN + "Web/HTTP/Reference/Status/403"),
         checked_at=D, terms=["authentication", "authorization"]),

    dict(id="cors-response-header", type="fact",
         prompt="CORS 오류가 나요. Access-Control-Allow-Origin은 어디에 넣나요?",
         statements=["Access-Control-Allow-Origin은 브라우저가 요청에 붙여 보내는 헤더예요.",
                     "이 헤더는 서버가 응답에 붙여 '이 출처는 읽어도 된다'고 알려 줘요.",
                     "CORS는 브라우저가 지키는 규칙이라 서버끼리 부를 때는 이 오류가 나지 않아요."],
         wrong=0, correction="Access-Control-Allow-Origin은 서버가 보내는 응답 헤더입니다. 그래서 서버 설정을 고쳐야 합니다.",
         how_to_check="MDN 헤더 설명 표에서 '응답 헤더(Response header)'인지 확인하기",
         sources=S("MDN Access-Control-Allow-Origin", MDN + "Web/HTTP/Reference/Headers/Access-Control-Allow-Origin"),
         checked_at=D, terms=["cors", "api"]),

    dict(id="post-not-idempotent", type="fact",
         prompt="요청이 실패하면 자동으로 다시 보내도 되나요?",
         statements=["PUT과 DELETE는 여러 번 보내도 결과가 같은 멱등 메서드예요.",
                     "POST도 멱등이라 여러 번 보내도 안전해요.",
                     "멱등이 아닌 요청을 다시 보내면 주문이 두 번 생기는 일이 생길 수 있어요."],
         wrong=1, correction="POST는 멱등이 보장되지 않습니다. 다시 보내면 같은 것이 두 번 만들어질 수 있습니다.",
         how_to_check="MDN 용어집 Idempotent에서 메서드 목록 확인하기",
         sources=S("MDN Glossary · Idempotent", MDN + "Glossary/Idempotent"),
         checked_at=D, terms=["retry", "api"]),

    dict(id="json-no-comments", type="fact",
         prompt="설정 파일을 JSON으로 쓰는데 설명을 어떻게 남기나요?",
         statements=["JSON 문법에는 주석이 없어요.",
                     "JSON 파일에는 // 로 주석을 달 수 있어요.",
                     "설명이 꼭 필요하면 \"_comment\" 같은 칸을 따로 두거나 주석을 허용하는 다른 형식을 써요."],
         wrong=1, correction="표준 JSON에는 주석 문법이 없습니다. // 를 넣으면 표준 JSON 읽기 도구는 오류를 냅니다.",
         how_to_check="JSON 표준(RFC 8259)의 문법에 주석이 있는지 확인하기",
         sources=S("IETF RFC 8259 · JSON", "https://datatracker.ietf.org/doc/html/rfc8259"),
         checked_at=D, terms=["json", "configuration-management"]),

    # ---------------- 코드 (code) ----------------
    dict(id="js-array-includes", type="code",
         prompt="자바스크립트 배열에 값이 들어 있는지 어떻게 확인하나요?",
         statements=["배열은 contains()로 들어 있는지 확인해요.",
                     "includes()는 들어 있으면 true, 없으면 false를 돌려줘요.",
                     "indexOf()는 없으면 -1을 돌려줘요."],
         wrong=0, correction="자바스크립트 배열에는 contains()가 없습니다. includes()를 씁니다.",
         how_to_check="MDN Array 메서드 목록에서 이름 찾기, 또는 콘솔에서 직접 실행해 보기",
         sources=S("MDN Array.prototype.includes()", MDN + "Web/JavaScript/Reference/Global_Objects/Array/includes"),
         checked_at=D, terms=["hallucination", "frontend"]),

    dict(id="git-force-with-lease", type="code",
         prompt="다른 사람 작업을 덮어쓰지 않게 안전하게 강제 push하려면요?",
         statements=["git push --force-safe로 안전하게 덮어써요.",
                     "--force-with-lease는 원격이 내가 마지막으로 본 상태일 때만 덮어써요.",
                     "그냥 --force는 다른 사람이 올린 커밋을 지울 수 있어요."],
         wrong=0, correction="--force-safe라는 옵션은 없습니다. 안전한 강제 push는 --force-with-lease입니다.",
         how_to_check="git push --help 또는 git-scm.com의 git push 문서에서 옵션 찾기",
         sources=S("git-scm.com · git-push", "https://git-scm.com/docs/git-push"),
         checked_at=D, terms=["git", "hallucination"]),

    dict(id="python-append-returns-none", type="code",
         prompt="파이썬 목록에 값을 넣고 그 목록을 다시 담고 싶어요.",
         statements=["nums = nums.append(4)라고 쓰면 4가 들어간 새 목록이 담겨요.",
                     "append()는 목록 자체를 바꾸고 None을 돌려줘요.",
                     "nums.append(4)만 쓰면 nums에 4가 들어가요."],
         wrong=0, correction="append()는 None을 돌려줍니다. nums = nums.append(4)라고 쓰면 nums가 None이 됩니다.",
         how_to_check="파이썬 공식 튜토리얼에서 목록 메서드의 반환값 확인하기, 또는 직접 print해 보기",
         sources=S("Python Tutorial · Data Structures", "https://docs.python.org/3/tutorial/datastructures.html"),
         checked_at=D, terms=["edge-case", "unit-test"]),

    dict(id="fetch-404-not-reject", type="code",
         prompt="fetch로 API를 부를 때 404 같은 오류는 어떻게 잡나요?",
         statements=["fetch는 404가 오면 자동으로 catch로 넘어가요.",
                     "fetch는 네트워크 오류일 때만 실패(reject)해요.",
                     "그래서 response.ok나 response.status를 직접 확인해야 해요."],
         wrong=0, correction="fetch는 404나 500이 와도 실패하지 않습니다. response.ok를 확인해야 합니다.",
         how_to_check="MDN fetch() 설명에서 HTTP 오류 상태일 때 동작 확인하기",
         sources=S("MDN Window.fetch()", MDN + "Web/API/Window/fetch"),
         checked_at=D, terms=["api", "edge-case"]),

    dict(id="js-sort-default-string", type="code",
         prompt="자바스크립트로 숫자 배열을 작은 순서로 정렬하려면요?",
         statements=["[10, 9, 1].sort()는 [1, 9, 10]이 돼요.",
                     "sort()는 기본으로 값을 글자로 바꿔서 비교해요.",
                     "숫자는 sort((a, b) => a - b)처럼 비교 함수를 넣어 정렬해요."],
         wrong=0, correction="[10, 9, 1].sort()는 글자 순서로 비교해 [1, 10, 9]가 됩니다.",
         how_to_check="브라우저 콘솔에서 직접 실행해 보기, MDN sort() 설명 확인하기",
         sources=S("MDN Array.prototype.sort()", MDN + "Web/JavaScript/Reference/Global_Objects/Array/sort"),
         checked_at=D, terms=["edge-case", "unit-test"]),
]


# 정답(틀린 문장) 자리가 ①에 몰리면 찍어서 맞히게 된다 → 문제 순서대로 ①②③에 고르게 돌려 놓는다.
# 문장 내용은 그대로, 순서만 돌린다 (2026-11-24, 처음 쓴 상태: ① 13개 · ② 6개 · ③ 1개).
def _spread(checks):
    for i, c in enumerate(checks):
        target = i % 3
        shift = (c["wrong"] - target) % 3
        c["statements"] = c["statements"][shift:] + c["statements"][:shift]
        c["wrong"] = target
    return checks


AI_CHECKS = _spread(AI_CHECKS)
