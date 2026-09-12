# studyFinal — 미니 게시판 웹사이트

study0~10에서 하나씩 배운 것을 모두 합쳐, Notion 학습 목표에 있던 예제("Vue Todo / 게시판을 Reflex로 다시 만들기")를 실제로 구현합니다. `demo/`가 "개념 하나씩 연습하는 실습장"이었다면, `project/`는 `vue.js`/`react` 학습 저장소의 `project/`와 같은 위치 — **완결된 미니 웹사이트**입니다.

```
- [x] Reflex 프로젝트 생성과 실행
- [x] State 클래스로 화면 상태 관리
- [x] 이벤트 핸들러로 CRUD
- [x] 라우팅 / 페이지 분리
- [x] FastAPI 또는 Django API와 연동 가능성 확인
- [x] 배포 (도커 또는 Reflex 클라우드)
```

프로젝트 위치: [`project/`](./project)

---

## 1. 무엇을 만들었나

로그인한 사용자가 글을 쓰고, 본인 글만 수정/삭제할 수 있는 **미니 게시판**입니다.

| 페이지 | 경로 | 설명 |
|---|---|---|
| 목록 | `/` | 전체 게시글(제목/작성자/작성일) 목록. 누구나 볼 수 있음 |
| 로그인 | `/login` | 데모 계정으로 로그인 |
| 상세 | `/post/[post_id]` | 게시글 본문. 본인 글이면 수정/삭제 버튼이 보임 |
| 새 글 작성 | `/post/new` | 로그인한 사용자만 접근 가능 (보호된 페이지) |
| 글 수정 | `/post/[post_id]/edit` | 작성자 본인만 접근 가능 |

## 2. 폴더 구조

```
project/
├─ rxconfig.py           # study9: db_url, env_file, cors_allowed_origins
├─ requirements.txt       # reflex, sqlmodel, alembic, python-dotenv
├─ .env.example           # study9: 환경변수 템플릿
├─ Dockerfile, docker-entrypoint.sh, .dockerignore   # study10
├─ alembic/                # study7: DB 마이그레이션
└─ project/
   ├─ project.py          # 페이지 등록 (라우팅, study5)
   ├─ state.py            # 전역 State: 인증 + 게시글 CRUD
   ├─ models.py           # Post 테이블 정의 (study7)
   ├─ components/
   │  ├─ post_card.py     # 목록 카드 (study1~2 패턴)
   │  └─ post_form.py     # 작성/수정 공용 폼 (study4)
   └─ pages/
      ├─ index.py          # 목록 페이지
      ├─ login.py          # 로그인 페이지 (study8)
      ├─ post_detail.py    # 상세 페이지 (study5)
      ├─ post_new.py       # 작성 페이지
      └─ post_edit.py      # 수정 페이지
```

## 3. 각 study가 어디에 쓰였는지

- **study2 (State)**: `posts: list[dict]`가 화면의 유일한 데이터 원천입니다.
- **study3~4 (CRUD, 폼 분리/검증)**: `create_post`/`update_post`/`delete_post`, 그리고 두 페이지(작성/수정)가 공유하는 `post_form` 컴포넌트 + `_validate_form`(제목 필수/50자 제한, 내용 필수).
- **study5 (라우팅)**: `/post/[post_id]`, `/post/[post_id]/edit`처럼 동적 라우트로 게시글 id를 받고, `current_post` ComputedVar로 찾습니다.
- **study7 (DB)**: `models.py`의 `Post`(SQLModel), `rx.session()`으로 조회/저장, `alembic/`으로 스키마 관리.
- **study8 (인증/보호된 페이지)**: `is_logged_in`, `require_login` 대신 여기서는 `prepare_new_post`/`prepare_edit_post`가 같은 역할(로그인 확인 + 리다이렉트)을 합니다.
- **study9~10 (배포)**: `.env.example`, `Dockerfile`.

## 4. 이 프로젝트에서 새로 강조한 것 — "화면에서 숨기기"와 "서버에서 막기"는 다르다

`post_detail.py`는 `can_edit_current_post`가 참일 때만 수정/삭제 버튼을 **보여줍니다**. 하지만 그것만으로는 부족합니다. 버튼을 안 보여줘도, 다른 사용자가 브라우저 개발자 도구나 API 호출로 `update_post`/`delete_post`를 직접 실행하려 할 수 있습니다.

그래서 실제 방어는 **이벤트 핸들러(서버) 안에서 다시 한번** 이루어집니다.

```python
# state.py
@rx.event
def update_post(self):
    ...
    with rx.session() as session:
        record = session.get(Post, post_id)
        if record is None or record.author != self.current_username:
            return rx.redirect("/")   # 본인 글이 아니면 여기서 다시 막는다
        ...

@rx.event
def delete_post(self, post_id: int):
    with rx.session() as session:
        record = session.get(Post, post_id)
        if record is not None and record.author == self.current_username:
            session.delete(record)
            session.commit()
    # 조건에 안 맞으면 조용히 아무 일도 안 일어난다
```

**"화면에 안 보이게 하는 것"은 UX이고, "서버 로직에서 조건을 확인하는 것"이 진짜 보안입니다.** 이 원칙은 Vue/React를 포함한 모든 클라이언트-서버 구조 웹앱에 공통으로 적용됩니다.

## 5. 실행 방법

```bash
cd project
python -m venv .venv && source .venv/Scripts/activate   # Windows(Git Bash) 기준
pip install -r requirements.txt

reflex db init      # alembic/이 이미 있다면 생략
reflex db migrate   # DB 테이블 생성

reflex run
```

- `http://localhost:3000/login` → `demo` / `reflex123`으로 로그인
- "새 글 작성" → 제목/내용 입력 후 작성 → 상세 페이지로 이동하는지 확인
- 목록으로 돌아가서 방금 쓴 글이 맨 위에 보이는지 확인 (최신순 정렬)
- 다른 계정(`guest` / `guest123`)으로 로그인해서, `demo` 계정이 쓴 글의 상세 페이지에 수정/삭제 버튼이 **보이지 않는지** 확인
- `guest`로 로그인한 상태에서 `demo`가 쓴 글의 `/post/{id}/edit` 주소를 직접 입력해서 들어가도 목록으로 튕기는지 확인 (4절에서 설명한 서버 측 검증)

## 6. 더 나아가기 (선택 과제)

이 프로젝트는 학습용으로 범위를 좁혔습니다. 실제 서비스 수준으로 확장한다면:

- **비밀번호 해시**: `DEMO_USERS` 평문 비교 대신 `passlib`/`bcrypt`로 해시 저장 + 검증, 회원가입 페이지 추가
- **댓글 기능**: `Comment` 모델(외래키로 `Post` 참조) 추가 — study7에서 배운 마이그레이션 과정을 한 번 더 연습하기 좋은 주제
- **페이지네이션**: 게시글이 많아지면 `session.exec(select(Post).offset(...).limit(...))`로 목록을 나눠 가져오기
- **검색**: 제목/내용 검색 입력창 + `where(Post.title.contains(keyword))`
- **study6 응용**: 게시글 등록 시 외부 API(예: 욕설/스팸 필터링 서비스)를 호출해 내용을 검사하는 기능 추가

여기까지가 이 저장소의 Python Reflex 학습 과정입니다. `study0`(React 기초 이론)부터 시작해 Reflex의 기본기, 고급 기능, 배포까지 다뤘고, 그 결과물이 이 `project/` 미니 게시판입니다.
