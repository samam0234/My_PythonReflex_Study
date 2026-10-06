# Python Reflex 학습 저장소

Python 코드만으로 UI + 상태 + 이벤트를 다루는 [Reflex](https://reflex.dev) 학습 기록입니다. (Reflex 0.9.11 기준)

| 위치 | 설명 |
|---|---|
| `study0.md` | Reflex 이해를 위한 React 기초 이론 |
| `study1.md` ~ `study5.md` | 기본기 실습: 프로젝트 생성, State, CRUD, 폼/컴포넌트 분리, 라우팅 |
| `study6.md` ~ `study10.md` | 고급: 외부 FastAPI 연동, DB(SQLModel+Alembic), 로그인, 환경설정/빌드, Docker/Reflex Cloud |
| `studyFinal.md` | 종합 프로젝트: 미니 게시판 |
| [`demo/`](./demo) | study1~9 실습 코드가 누적된 Reflex 프로젝트 |
| [`project/`](./project) | studyFinal의 완결된 미니 게시판 웹사이트 |
| `.agent/`, `.claude/`, `.codex/`, `.grok/` | AI 에이전트 인수인계 문서 / 커밋 규칙 |

## 빠른 시작

```bash
cd project            # 또는 demo
python -m venv .venv && source .venv/Scripts/activate   # Windows(Git Bash) 기준
pip install -r requirements.txt
reflex db migrate     # DB 테이블 생성
reflex run            # http://localhost:3000
```

Windows에서 `UnicodeEncodeError`가 나면 `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8` 환경변수를 설정하세요.
