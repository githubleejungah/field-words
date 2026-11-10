"""필드워드 종합 점검 — 버그·보안·내용을 한 번에 검사하고 보고서를 남긴다.

실행: python pipeline/check_all.py
결과: 화면에 요약 + pipeline/reports/점검_YYYY-MM-DD.md (Git에 올리지 않음)
     오류가 있으면 종료 코드 1

검사 항목
  1. 데이터      glossary.json 스키마·참조 검사 (validate.py)
  2. 규칙 시험    학습 기록 규칙 단위 테스트 (node --test)
  3. 비밀 값      API 키·토큰·비밀 키가 저장소에 들어 있는지
  4. 개인정보     공개 사이트 파일에 전화번호·주민번호·모르는 이메일이 있는지
  5. 금지 파일    .env, research/ 가 Git에 올라가 있는지
  6. 캐시 버전    js·css를 고쳤는데 index.html의 ?v= 를 안 올렸는지
  7. 외부 파일    공개 사이트가 외부 서버의 스크립트를 불러오는지 (공급망 위험)
  8. 의존성       파이썬 라이브러리에 새 버전이 있는지 (인터넷이 없으면 건너뜀)
  9. 내용 보강    모범 답변·함정이 빠졌거나 오래된 용어, 단계별 용어 수
"""
import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
REPORTS = ROOT / "pipeline" / "reports"
sys.path.insert(0, str(ROOT / "pipeline"))
import validate  # noqa: E402

results = []   # (구분, 등급, 내용)  등급: 오류 / 경고 / 통과 / 정보


def add(kind, level, text):
    results.append((kind, level, text))


def run(cmd, timeout=120):
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except (OSError, subprocess.TimeoutExpired) as e:
        return -1, str(e)


def tracked_files():
    code, out = run(["git", "-c", "core.quotepath=false", "ls-files"])
    return [ROOT / line for line in out.splitlines() if line.strip()] if code == 0 else []


# ---------- 1. 데이터 ----------
def check_data():
    schema = json.loads(validate.SCHEMA_PATH.read_text(encoding="utf-8"))
    data = json.loads(validate.DATA_PATH.read_text(encoding="utf-8"))
    errors = validate.check_schema(data, schema)
    warnings = []
    if not errors:
        ref_errors, warnings = validate.check_references(data)
        errors += ref_errors
    for e in errors:
        add("데이터", "오류", e)
    for w in warnings:
        add("데이터", "경고", w)
    if not errors:
        add("데이터", "통과", f"용어 {len(data['terms'])}개, 혼동 쌍 {len(data['confusable_pairs'])}개")
    return data


# ---------- 2. 규칙 시험 ----------
def check_tests():
    code, out = run(["node", "--test", "tests/review.test.js"])
    passed = re.search(r"ℹ pass (\d+)", out)
    failed = re.search(r"ℹ fail (\d+)", out)
    if code == -1:
        add("규칙 시험", "경고", "Node.js를 실행하지 못해 시험을 건너뛰었습니다.")
    elif failed and int(failed.group(1)) > 0:
        add("규칙 시험", "오류", f"단위 테스트 {failed.group(1)}개 실패. `node --test tests/review.test.js`로 확인하세요.")
    else:
        add("규칙 시험", "통과", f"단위 테스트 {passed.group(1) if passed else '?'}개 통과")


# ---------- 3. 비밀 값 ----------
SECRET_PATTERNS = {
    "Anthropic API 키": r"sk-ant-[A-Za-z0-9_\-]{20,}",
    "OpenAI 형식 키": r"\bsk-[A-Za-z0-9]{32,}",
    "AWS 접근 키": r"\bAKIA[0-9A-Z]{16}\b",
    "구글 API 키": r"\bAIza[0-9A-Za-z_\-]{35}\b",
    "GitHub 토큰": r"\bgh[pousr]_[A-Za-z0-9]{30,}",
    "비밀 키 파일": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "비밀 값 대입": r"(?i)\b(api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']",
}
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".mp3", ".woff", ".woff2"}


def check_secrets(files):
    found = 0
    for f in files:
        if f.suffix in SKIP_SUFFIX or not f.is_file() or f.name == "check_all.py":
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for name, pat in SECRET_PATTERNS.items():
            for m in re.finditer(pat, text):
                line = text.count("\n", 0, m.start()) + 1
                add("비밀 값", "오류", f"{name} 의심: {f.relative_to(ROOT)}:{line} — 사실이면 키를 바로 폐기하고 새로 발급하세요.")
                found += 1
    if not found:
        add("비밀 값", "통과", f"Git에 올라간 파일 {len(files)}개에서 비밀 값 없음")


# ---------- 4. 개인정보 (공개 사이트) ----------
ALLOWED_EMAILS = {"veryfar4@gmail.com", "name@example.com"}   # 의견 받는 메일(사용자 지정), 입력 칸 예시
PII_PATTERNS = {
    "휴대폰 번호": r"\b01[016789][-\s]?\d{3,4}[-\s]?\d{4}\b",
    "주민등록번호": r"\b\d{6}-[1-4]\d{6}\b",
}


def check_privacy():
    hits = 0
    for f in SITE.rglob("*"):
        if not f.is_file() or f.suffix in SKIP_SUFFIX:
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        rel = f.relative_to(ROOT)
        for name, pat in PII_PATTERNS.items():
            for m in re.finditer(pat, text):
                add("개인정보", "오류", f"{name} 의심: {rel} — '{m.group(0)}'")
                hits += 1
        for m in re.finditer(r"[\w.+-]+@[\w-]+\.[\w.]+", text):
            if m.group(0) not in ALLOWED_EMAILS:
                add("개인정보", "경고", f"허용 목록에 없는 이메일: {rel} — '{m.group(0)}'")
                hits += 1
    if not hits:
        add("개인정보", "통과", "공개 사이트 파일에 개인정보 없음")


# ---------- 5. 금지 파일 ----------
def check_forbidden(files):
    bad = [f for f in files if f.name == ".env" or "research" in f.relative_to(ROOT).parts[:1]]
    for f in bad:
        add("금지 파일", "오류", f"Git에 올라가면 안 되는 파일: {f.relative_to(ROOT)}")
    if not bad:
        add("금지 파일", "통과", ".env, research/ 가 Git에 없음")


# ---------- 6. 캐시 버전 ----------
def check_cache_version():
    code, out = run(["git", "-c", "core.quotepath=false", "diff", "--name-only", "HEAD"])
    if code != 0:
        add("캐시 버전", "경고", "Git 변경 목록을 읽지 못했습니다.")
        return
    changed = out.split()
    code_changed = [c for c in changed if re.match(r"site/(js|css)/", c)]
    if not code_changed:
        add("캐시 버전", "통과", "고친 js·css 없음")
        return
    _, diff = run(["git", "diff", "HEAD", "--", "site/index.html"])
    if "?v=" in diff:
        add("캐시 버전", "통과", "js·css를 고쳤고 ?v= 도 올렸습니다")
    else:
        add("캐시 버전", "오류", f"{', '.join(code_changed)} 를 고쳤는데 site/index.html의 ?v= 를 올리지 않았습니다. 사용자가 옛 화면을 봅니다.")


# ---------- 7. 외부 파일 ----------
def check_external():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    ext = re.findall(r"""<(?:script|link)[^>]+(?:src|href)=["'](https?://[^"']+)""", html)
    for url in ext:
        add("외부 파일", "경고", f"외부 서버 파일을 불러옵니다: {url} — 그 서버가 바뀌면 우리 사이트도 바뀝니다. 버전 고정·무결성 값(SRI)을 확인하세요.")
    if not ext:
        add("외부 파일", "통과", "외부 스크립트·스타일 없음 (직접 만든 코드만 사용)")


# ---------- 8. 의존성 ----------
def check_dependencies():
    venv_py = ROOT / ".venv" / "Scripts" / "python.exe"
    py = str(venv_py) if venv_py.exists() else sys.executable
    code, out = run([py, "-m", "pip", "list", "--outdated", "--format=json", "--disable-pip-version-check"], timeout=60)
    try:
        items = json.loads(out.strip().splitlines()[-1]) if code == 0 and out.strip() else None
    except (json.JSONDecodeError, IndexError):
        items = None
    if items is None:
        add("의존성", "정보", "새 버전 확인을 건너뛰었습니다 (인터넷 연결 또는 pip 문제).")
        return
    watch = [i for i in items if i["name"].lower() in {"jsonschema", "referencing", "jsonschema-specifications", "rpds-py", "attrs"}]
    for i in watch:
        add("의존성", "경고", f"{i['name']} {i['version']} → {i['latest_version']} 새 버전이 있습니다. 변경 내역을 확인하고 올리세요.")
    if not watch:
        add("의존성", "통과", "검사 도구 라이브러리가 최신입니다")


# ---------- 9. 내용 보강 ----------
STAGES = ["discovery", "design", "build", "test", "deploy", "operate", "secure", "grow", "automate"]


def check_content(data):
    terms = [t for t in data["terms"] if not t.get("replaced_by")]
    counts = {s: sum(1 for t in terms if t["stage"] == s) for s in STAGES}
    add("내용 보강", "정보", "단계별 용어 수: " + ", ".join(f"{s} {n}" for s, n in counts.items()))
    thin = [s for s, n in counts.items() if n < 5]
    if thin:
        add("내용 보강", "정보", f"용어가 5개보다 적은 단계(다음 추가 우선): {', '.join(thin)}")
    no_answer = [t["id"] for t in terms if not t.get("interview_a")]
    no_pitfall = [t["id"] for t in terms if not t.get("pitfall")]
    if no_answer:
        add("내용 보강", "정보", f"30초 모범 답변이 없는 용어 {len(no_answer)}개: {', '.join(no_answer[:15])}")
    if no_pitfall:
        add("내용 보강", "정보", f"현업 함정이 없는 용어 {len(no_pitfall)}개: {', '.join(no_pitfall[:15])}")
    old = [t["id"] for t in terms if (date.today() - date.fromisoformat(t["updated_at"])).days > 90]
    if old:
        add("내용 보강", "정보", f"90일 넘게 고치지 않은 용어 {len(old)}개 (최신 내용인지 확인): {', '.join(old[:15])}")


def write_report():
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / f"점검_{date.today().isoformat()}.md"
    errors = sum(1 for r in results if r[1] == "오류")
    warns = sum(1 for r in results if r[1] == "경고")
    lines = [f"# 필드워드 종합 점검 {datetime.now():%Y-%m-%d %H:%M}", "",
             f"- 오류 {errors}개 · 경고 {warns}개", ""]
    for kind in dict.fromkeys(r[0] for r in results):
        lines.append(f"## {kind}")
        lines += [f"- [{lvl}] {text}" for k, lvl, text in results if k == kind]
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path, errors, warns


def main():
    files = tracked_files()
    data = check_data()
    check_tests()
    check_secrets(files)
    check_privacy()
    check_forbidden(files)
    check_cache_version()
    check_external()
    check_dependencies()
    check_content(data)

    path, errors, warns = write_report()
    icon = {"오류": "❌", "경고": "⚠️ ", "통과": "✅", "정보": "ℹ️ "}
    for kind, lvl, text in results:
        print(f"{icon[lvl]} [{kind}] {text}")
    print(f"\n오류 {errors}개 · 경고 {warns}개 → 보고서: {path.relative_to(ROOT)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
