# study7 (고급2) — 데이터베이스 연동 (실습)

study6까지 `self.fruits`는 서버 프로세스가 재시작되면 초기값으로 리셋되는 **메모리 상의 데이터**였습니다. 이번 단계에서 진짜 데이터베이스(SQLite)에 저장하도록 바꿉니다.

```
- [x] Reflex 프로젝트 생성과 실행
- [x] State 클래스로 화면 상태 관리
- [x] 이벤트 핸들러로 CRUD
- [x] 라우팅 / 페이지 분리
- [x] FastAPI 또는 Django API와 연동 가능성 확인
- [ ] 배포 (도커 또는 Reflex 클라우드)     (study9~10 예정)
```

대응 실습: 신규 [`demo/demo/models.py`](./demo/demo/models.py) / 변경 [`state.py`](./demo/demo/state.py), [`rxconfig.py`](./demo/rxconfig.py), [`demo.py`](./demo/demo/demo.py) / 신규 `demo/alembic/` (마이그레이션)

---

## 1. 중요: `rx.Model`은 지원 종료(deprecated)되었다

인터넷에 있는 예전 Reflex 튜토리얼 다수가 `class Fruit(rx.Model, table=True): ...`처럼 `rx.Model`을 씁니다. 하지만 이 저장소가 쓰는 Reflex 0.9.11에서 `rx.Model`을 상속하면 다음 경고가 뜹니다.

```
DeprecationWarning: reflex.Model — Directly use database ORM layer, like sqlalchemy or SQLModel
```

그래서 이 문서는 **SQLModel을 직접** 씁니다. Reflex는 모델 정의에 관여하지 않고, `rx.session()`으로 "설정 파일(`rxconfig.py`)의 `db_url`에 연결된 세션"만 대신 만들어줍니다.

```python
# demo/models.py
import sqlmodel

class FruitRecord(sqlmodel.SQLModel, table=True):
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    name: str
    in_stock: bool = True
```

## 2. DB 설정 및 마이그레이션 명령어

```python
# rxconfig.py
config = rx.Config(
    app_name="demo",
    db_url="sqlite:///reflex.db",   # 이 한 줄이 없으면 db_url이 None
    ...
)
```

```bash
pip install sqlmodel alembic     # requirements.txt에도 추가
reflex db init                   # alembic 초기화 + 첫 마이그레이션 스크립트 자동 생성
reflex db migrate                # 마이그레이션 적용 → reflex.db 파일 생성, 테이블 생성
```

- `reflex db init`: 내부적으로 [Alembic](https://alembic.sqlalchemy.org/)(SQLAlchemy 진영의 마이그레이션 도구)을 초기화합니다. 프로젝트에 `alembic/`, `alembic.ini`가 생기고, 현재 정의된 모델(`FruitRecord`)을 보고 **첫 마이그레이션 스크립트**(`alembic/versions/xxxx_.py`)를 자동 생성합니다.
- `reflex db migrate`: 아직 적용되지 않은 마이그레이션들을 실제 DB에 적용합니다 (테이블 생성/변경). 모델을 수정한 뒤에는 `reflex db makemigrations`로 변경분 스크립트를 새로 만들고 다시 `migrate`합니다.
- `reflex.db`(SQLite 파일)는 `.gitignore`에 이미 포함되어 있어 커밋되지 않습니다. **커밋해야 하는 것은 `alembic/`의 마이그레이션 스크립트**입니다 — 이게 있어야 다른 사람의 컴퓨터에서도 `reflex db migrate` 한 번으로 같은 스키마를 재현할 수 있습니다 (Django의 `migrations/` 폴더와 같은 위치).

## 3. `rx.session()`으로 DB 읽기/쓰기

```python
# state.py
import sqlmodel
from .models import FruitRecord

@rx.event
def load_fruits(self):
    with rx.session() as session:
        records = session.exec(sqlmodel.select(FruitRecord)).all()
        if not records:
            records = [FruitRecord(**seed) for seed in SEED_FRUITS]
            session.add_all(records)
            session.commit()
            for record in records:
                session.refresh(record)
        self.fruits = [record.model_dump() for record in records]
```

- `rx.session()`은 `with` 블록 안에서 쓰는 평범한 SQLModel `Session`입니다. `session.exec(select(...))`, `session.add(...)`, `session.commit()` 등 SQLAlchemy/SQLModel 사용법 그대로입니다 — **Reflex 고유 문법이 아닙니다.**
- 핵심은 마지막 줄입니다: `self.fruits = [record.model_dump() for record in records]`. DB에서 읽은 SQLModel 객체를 **그대로 State에 넣지 않고, `dict`로 변환**해서 넣습니다. 이렇게 하면 `fruit_card`, `fruit_badge` 등 지금까지 만든 컴포넌트를 **한 줄도 안 고치고 그대로 재사용**할 수 있습니다 — study2부터 `fruits`는 항상 "id/name/in_stock을 가진 dict의 리스트"였고, 그 값의 출처가 고정 리스트 → 메모리 State → DB로 바뀌었을 뿐 **모양은 그대로**이기 때문입니다.

## 4. CRUD 핸들러 — "원본(DB)을 바꾸고, 캐시(State)를 새로고침"

```python
@rx.event
def toggle_stock(self, fruit_id: int):
    with rx.session() as session:
        record = session.get(FruitRecord, fruit_id)
        if record is not None:
            record.in_stock = not record.in_stock
            session.add(record)
            session.commit()
    self.load_fruits()   # DB를 바꾼 뒤, State를 최신 DB 상태로 다시 채운다
```

- study2~6에서는 `self.fruits` 리스트/딕셔너리를 직접 수정하는 것으로 충분했습니다(그 자체가 유일한 데이터였으니까). 이제는 **DB가 진짜 원본**이므로, 순서가 "①DB 수정 → ②`load_fruits()`로 State를 다시 채움"으로 바뀝니다.
- 같은 클래스 안에서 `self.load_fruits()`처럼 **다른 이벤트 핸들러를 그냥 메서드처럼 호출**할 수 있습니다. 클릭 이벤트 하나로 "DB 갱신 + 화면 갱신"을 순서대로 처리하는 흔한 패턴입니다.

## 5. 페이지 로드 시 데이터 채우기 — `on_load`

```python
# demo.py
app.add_page(index, route="/", on_load=State.load_fruits)
app.add_page(fruit_detail, route="/fruit/[fruit_id]", on_load=State.load_fruits)
```

- `on_load`는 Vue Router의 네비게이션 가드(`beforeEnter`), React Router의 `loader`와 비슷한 역할입니다: **이 페이지에 진입할 때 자동으로 실행할 이벤트 핸들러**를 지정합니다.
- 이게 없으면 `self.fruits`는 빈 리스트인 채로 남아있고, 화면에 아무것도 안 뜹니다 — DB 연동 후 흔히 겪는 실수이니 기억해둡니다.

## 6. 실행 확인

```bash
cd demo
pip install -r requirements.txt
reflex db init      # 최초 1회 (alembic/ 이 이미 있다면 생략)
reflex db migrate    # 최초 1회 (또는 모델 변경 후)
reflex run
```

- 브라우저로 `http://localhost:3000/` 접속 → 사과/바나나/포도가 뜨는지 확인 (DB가 비어있었다면 이때 시드 데이터가 자동으로 채워짐)
- 새 과일을 추가하고, **`reflex run`을 껐다가 다시 실행** → 추가했던 과일이 그대로 남아있는지 확인 (메모리 State였던 study6까지는 재시작하면 사라졌지만, 이제는 DB에 저장되어 유지됨)
- 터미널에서 `sqlite3 demo/reflex.db "select * from fruitrecord;"` (또는 Python `sqlite3` 모듈)로 실제 테이블에 데이터가 들어있는지 직접 확인

## 7. 다음 단계 (study8, 고급3 예정)

- 지금까지는 모든 방문자가 같은 과일 목록을 봤습니다. study8에서 **로그인 상태**를 추가해서, 로그인한 사용자만 접근할 수 있는 "보호된 페이지"를 만듭니다.
