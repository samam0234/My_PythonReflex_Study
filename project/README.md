# project — Reflex 미니 게시판

`studyFinal.md`의 종합 프로젝트입니다. 로그인한 사용자가 글을 쓰고, 본인 글만 수정/삭제할 수 있습니다.

```bash
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
reflex db migrate
reflex run                                    # http://localhost:3000
```

- 데모 계정: `demo` / `reflex123`, `guest` / `guest123` (학습용 평문 비교 — 실서비스 금지)
- 페이지: `/` 목록, `/login`, `/post/[id]` 상세, `/post/new` 작성, `/post/[id]/edit` 수정
- Docker: `docker build -t reflex-board .` 후 `docker run -p 3000:3000 reflex-board`
