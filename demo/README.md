# demo — Reflex 실습 프로젝트

`study1.md` ~ `study9.md`의 실습이 누적된 프로젝트입니다. 과일 재고 목록을 소재로 State, CRUD, 폼 검증, 라우팅, 외부 API, DB, 로그인, 환경설정을 차례로 붙였습니다.

```bash
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
reflex db migrate
reflex run                                    # http://localhost:3000
uvicorn external_api.main:app --port 8001     # study6 외부 API (선택, external_api/requirements.txt 필요)
```

- 로그인 데모 계정: `demo` / `reflex123`
- `.env.example`을 `.env`로 복사해 설정을 덮어쓸 수 있습니다 (study9)
- Docker: `docker build -t reflex-demo .` (study10)
