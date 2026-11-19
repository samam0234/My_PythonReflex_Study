import json
import os
import re
import uuid
from pathlib import Path

import pytest
from playwright.sync_api import expect

KIND = os.getenv("REFLEX_E2E_APP", "project")
pytestmark = pytest.mark.e2e


def login(page, app_url, username="demo"):
    page.goto(app_url + "/login")
    password = (
        f"{username}-password-123"
        if KIND == "project"
        else {"demo": "reflex123", "guest": "guest123"}[username]
    )
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="password"]').fill(password)
    page.get_by_role("button", name="로그인", exact=True).click()
    expect(page).to_have_url(app_url + "/", timeout=20000)
    expect(page.get_by_role("button", name="로그아웃")).to_be_visible()


@pytest.mark.skipif(KIND == "demo", reason="게시판 앱 전용")
def test_login_crud_and_other_owner(app_url, page, browser):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(app_url + "/post/new")
    expect(page).to_have_url(app_url + "/login")
    page.locator('input[name="username"]').fill("demo")
    page.locator('input[name="password"]').fill("wrong-password-123")
    page.get_by_role("button", name="로그인", exact=True).click()
    expect(page.get_by_text("아이디 또는 비밀번호가 올바르지 않습니다.")).to_be_visible()
    login(page, app_url)
    page.get_by_role("link", name="새 글 작성", exact=True).click()
    title = "E2E " + uuid.uuid4().hex[:10]
    page.locator('input[name="title"]').fill(title)
    page.locator('textarea[name="content"]').fill("브라우저에서 작성한 본문")
    page.get_by_role("button", name="작성 완료").click()
    expect(page.get_by_role("heading", name=title, exact=True)).to_be_visible()
    detail_url = page.url
    page.reload()
    expect(page.get_by_text("브라우저에서 작성한 본문", exact=True)).to_be_visible()
    other_context = browser.new_context()
    other = other_context.new_page()
    try:
        login(other, app_url, "guest")
        other.goto(detail_url)
        expect(other.get_by_role("button", name="삭제", exact=True)).to_have_count(0)
        other.goto(detail_url + "/edit")
        expect(other.get_by_role("button", name="수정 완료", exact=True)).to_have_count(0)
    finally:
        other_context.close()
    page.get_by_role("link", name="수정", exact=True).click()
    page.locator('input[name="title"]').fill(title + " 수정")
    page.get_by_role("button", name="수정 완료").click()
    expect(page.get_by_role("heading", name=title + " 수정", exact=True)).to_be_visible()
    artifact = Path(os.getenv("REFLEX_E2E_ARTIFACTS", "artifacts"))
    artifact.mkdir(exist_ok=True)
    page.screenshot(path=str(artifact / f"{KIND}-detail.png"), full_page=True)
    page.get_by_role("button", name="삭제", exact=True).click()
    expect(page).to_have_url(app_url + "/")
    expect(page.get_by_role("heading", name=title + " 수정", exact=True)).to_have_count(0)
    page.get_by_role("button", name="로그아웃").click()
    page.goto(detail_url + "/edit")
    expect(page).to_have_url(app_url + "/login")
    assert errors == []


@pytest.mark.skipif(KIND != "project", reason="최종 앱 전용")
def test_mcp_readonly_dashboard(app_url, page):
    page.goto(app_url + "/dashboard")
    page.get_by_role("button", name="MCP 연결 확인").click()
    expect(page.locator("#mcp-result")).to_have_text(
        "Reflex 학습용 읽기 전용 도구가 연결되었습니다.", timeout=20000
    )


@pytest.mark.skipif(KIND != "project", reason="최종 앱 전용")
def test_invalid_id_and_ops_denied(app_url, page):
    page.goto(app_url + "/post/abc")
    expect(page.get_by_text("게시글을 찾을 수 없습니다.", exact=True)).to_be_visible()
    page.goto(app_url + "/ops")
    expect(page.get_by_text("로그인이 필요합니다.", exact=True)).to_be_visible()
    response = page.request.get(app_url + "/health/ready")
    # 개발 모드는 backend 포트로 health를 확인한다. 프로덕션은 동일 origin이다.
    if response.headers.get("content-type", "").startswith("application/json"):
        assert response.json() == {"status": "ready"}


@pytest.mark.skipif(KIND != "demo", reason="단원 앱 전용")
def test_lesson_events_forms_and_cache(app_url, page):
    page.goto(app_url + "/study1")
    for _ in range(3):
        page.get_by_role("button", name="증가", exact=True).click()
    expect(page.get_by_text(re.compile("클릭 수:"))).to_contain_text("3")
    page.goto(app_url + "/study3")
    page.get_by_role("button", name="추가", exact=True).click()
    expect(page.get_by_text("항목 1", exact=True)).to_be_visible()
    page.get_by_role("button", name="표시 전환").click()
    expect(page.get_by_text("목록 숨김", exact=True)).to_be_visible()
    page.goto(app_url + "/study5")
    page.locator('input[name="title"]').fill("폼 연습")
    page.locator('textarea[name="content"]').fill("본문")
    page.get_by_role("button", name="저장", exact=True).click()
    expect(page.get_by_text(re.compile("저장된 제목:"))).to_contain_text("폼 연습")
    page.goto(app_url + "/study6")
    page.locator('input[name="title"]').fill("DB 연습")
    page.locator('input[name="content"]').fill("본문")
    page.get_by_role("button", name="등록", exact=True).click()
    expect(page.get_by_text("DB 연습", exact=True)).to_be_visible()
    page.get_by_role("button", name="제목 수정", exact=True).click()
    expect(page.get_by_text("수정한 제목", exact=True)).to_be_visible()
    page.get_by_role("button", name="삭제", exact=True).click()
    expect(page.get_by_text("수정한 제목", exact=True)).to_have_count(0)
    page.goto(app_url + "/study11")
    page.get_by_role("button", name="조회", exact=True).click()
    expect(page.get_by_text("조회 완료", exact=True)).to_be_visible(timeout=15000)
    page.get_by_role("button", name="캐시 비우기").click()
    page.get_by_role("button", name="조회", exact=True).click()
    expect(page.get_by_role("button", name="조회", exact=True)).to_be_enabled(timeout=15000)


@pytest.mark.skipif(KIND != "project", reason="최종 앱 전용")
def test_pagination_and_search(app_url, page):
    from project.models import Post
    from project.services.database import open_session
    from sqlmodel import select

    with open_session() as session:
        session.add_all(
            [
                Post(title=f"페이징 {i:02}", content="본문", author="e2e-pagination")
                for i in range(25)
            ]
        )
        session.commit()
    try:
        page.goto(app_url + "/")
        expect(page.get_by_text("1 / 2 페이지 · 25개", exact=True)).to_be_visible()
        page.get_by_role("button", name="다음", exact=True).click()
        expect(page.get_by_text("2 / 2 페이지 · 25개", exact=True)).to_be_visible()
        page.locator('input[name="search"]').fill("페이징 03")
        page.get_by_role("button", name="검색", exact=True).click()
        expect(page.get_by_text("1 / 1 페이지 · 1개", exact=True)).to_be_visible()
        expect(page.get_by_role("heading", name="페이징 03", exact=True)).to_be_visible()
    finally:
        with open_session() as session:
            for record in session.exec(select(Post).where(Post.author == "e2e-pagination")).all():
                session.delete(record)
            session.commit()


@pytest.mark.skipif(KIND != "demo", reason="단원 앱 전용")
def test_lesson_auth_routing_and_chart(app_url, page):
    page.goto(app_url + "/study4/post/abc")
    expect(page.get_by_text("올바른 글 번호가 아닙니다.", exact=True)).to_be_visible()
    page.goto(app_url + "/study7")
    page.locator('input[name="title"]').fill("인증 연습")
    page.locator('input[name="content"]').fill("본문")
    page.get_by_role("button", name="등록", exact=True).click()
    expect(page).to_have_url(app_url + "/study7/login")
    page.locator('input[name="username"]').fill("demo")
    page.locator('input[name="password"]').fill("reflex123")
    page.get_by_role("button", name="로그인", exact=True).click()
    expect(page).to_have_url(app_url + "/study7")
    page.locator('input[name="title"]').fill("인증 연습")
    page.locator('input[name="content"]').fill("본문")
    page.get_by_role("button", name="등록", exact=True).click()
    expect(page.get_by_text("인증 연습", exact=True)).to_be_visible()
    page.goto(app_url + "/study13")
    expect(page.locator(".recharts-bar-rectangle")).to_have_count(3)
    page.get_by_role("combobox").click()
    page.get_by_role("option", name="오늘", exact=True).click()
    expect(page.locator(".recharts-bar-rectangle")).to_have_count(1)


@pytest.mark.skipif(KIND != "demo", reason="단원 앱 전용")
def test_todo_and_http_refresh_lab(app_url, page):
    page.goto(app_url + "/study3/todo")
    expect(page.get_by_text("할 일이 없습니다.")).to_be_visible()
    page.get_by_role("button", name="추가").click()
    expect(page.get_by_role("alert")).to_have_text("할 일을 1~80자로 입력하세요.")
    page.get_by_placeholder("할 일").fill("노션 항목 검증")
    page.get_by_role("button", name="추가").click()
    expect(page.locator("#todo-remaining")).to_have_text("남은 할 일: 1")
    page.get_by_role("button", name="완료 전환").click()
    expect(page.locator("#todo-remaining")).to_have_text("남은 할 일: 0")
    expect(page.get_by_text("완료", exact=True)).to_be_visible()
    page.get_by_role("button", name="삭제", exact=True).click()
    expect(page.get_by_text("할 일이 없습니다.")).to_be_visible()

    page.goto(app_url + "/study11")
    for case, statuses, result in (
        ("갱신 성공", "401 → 200 → 200", "갱신 후 조회 성공"),
        ("갱신 거부", "401 → 401", "실습 세션 만료 · 다시 로그인하세요."),
        ("재요청 거부", "401 → 200 → 401", "실습 세션 만료 · 다시 로그인하세요."),
    ):
        page.get_by_role("button", name=case, exact=True).click()
        expect(page.locator("#refresh-status")).to_have_text(statuses)
        expect(page.get_by_role("status")).to_have_text(result)


@pytest.mark.skipif(KIND != "project", reason="최종 앱 성능 측정")
def test_record_page_script_transfer(app_url, browser):
    results = {}
    for route in ("/", "/dashboard"):
        context = browser.new_context()
        try:
            page = context.new_page()
            page.goto(app_url + route, wait_until="networkidle")
            sample = page.evaluate(
                """() => {
                    const scripts = performance.getEntriesByType("resource")
                        .filter(entry => new URL(entry.name).pathname.endsWith(".js"));
                    return {
                        scripts: scripts.length,
                        transfer_bytes: scripts.reduce((total, item) => total + item.transferSize, 0),
                        encoded_body_bytes: scripts.reduce((total, item) => total + item.encodedBodySize, 0),
                    };
                }"""
            )
            assert sample["scripts"] > 0
            assert sample["transfer_bytes"] > 0
            results[route] = sample
        finally:
            context.close()
    artifact = Path(os.getenv("REFLEX_E2E_ARTIFACTS", "artifacts"))
    artifact.mkdir(exist_ok=True)
    (artifact / "browser-script-transfer.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )


@pytest.mark.skipif(
    KIND != "demo" or os.getenv("BOARD_V1_VERIFY") != "1", reason="별도 FastAPI 실행 필요"
)
def test_v1_board_over_http(app_url, page):
    page.goto(app_url + "/study6/api-board")
    status = page.locator("#api-board-status")
    email = f"{uuid.uuid4().hex[:10]}@example.com"
    register = page.get_by_role("form", name="가입")
    register.get_by_placeholder("이메일").fill(email)
    register.get_by_placeholder("닉네임").fill("연동 실습")
    register.get_by_placeholder("비밀번호").fill("Test-password-123")
    register.get_by_role("button").click()
    expect(status).to_have_text("HTTP 201")
    login_form = page.get_by_role("form", name="로그인")
    login_form.get_by_placeholder("이메일").fill(email)
    login_form.get_by_placeholder("비밀번호").fill("Test-password-123")
    login_form.get_by_role("button").click()
    expect(page.get_by_role("button", name="로그아웃")).to_be_visible()
    create = page.get_by_role("form", name="글 작성")
    create.get_by_placeholder("제목").fill("연동 글")
    create.get_by_placeholder("본문").fill("별도 프로세스의 DB에 저장")
    create.get_by_role("button").click()
    expect(status).to_have_text("HTTP 201 · 작성 완료")
    edit = page.get_by_role("form", name="글 수정")
    edit.locator('input[name="title"]').fill("연동 글 수정")
    edit.get_by_role("button").click()
    expect(page.get_by_role("heading", name="연동 글 수정")).to_be_visible()
    page.get_by_placeholder("댓글", exact=True).fill("연동 댓글")
    page.get_by_role("button", name="댓글 등록").click()
    expect(page.get_by_text("연동 댓글", exact=True)).to_be_visible()
    page.get_by_role("button", name="댓글 삭제").click()
    expect(status).to_have_text("HTTP 204 · 댓글 삭제 완료")
    page.get_by_role("button", name="글 삭제").click()
    expect(status).to_have_text("HTTP 204 · 삭제 완료")
    page.get_by_role("button", name="로그아웃").click()
    expect(status).to_have_text("HTTP 204")
