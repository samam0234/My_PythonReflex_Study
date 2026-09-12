import os

import httpx
import reflex as rx
import sqlmodel

from .models import FruitRecord

# rx.Config 필드(db_url, cors_allowed_origins 등)는 REFLEX_* 환경변수로
# 자동 덮어쓰기 되지만, 이런 "우리 앱만의" 값은 os.environ에서 직접 읽는다.
# rxconfig.py의 env_file=".env" 설정 덕분에, .env 파일에 EXTERNAL_API_BASE_URL을
# 적어두면 여기서도 그대로 읽힌다.
EXTERNAL_API_BASE_URL = os.environ.get("EXTERNAL_API_BASE_URL", "http://127.0.0.1:8001")

# study8 실습용 데모 계정. 타입 어노테이션이 없는 클래스 속성이라
# Reflex가 State 값(Var)으로 취급하지 않는다 — 그냥 서버 쪽 상수다.
# 실제 서비스에서는 반드시 DB + 비밀번호 해시(passlib 등)를 써야 한다.
DEMO_USERS = {"demo": "reflex123"}

SEED_FRUITS = [
    {"name": "사과", "in_stock": True},
    {"name": "바나나", "in_stock": False},
    {"name": "포도", "in_stock": True},
]


class State(rx.State):
    """앱 전역 상태.

    study6까지 `fruits`는 서버 프로세스가 재시작되면 초기값으로 리셋되는
    "메모리 상의 데이터"였다. study7부터는 진짜 데이터베이스(SQLite)에서
    읽고 쓴다. `fruits`는 여전히 `list[dict]`이지만, 이제 이 값은
    DB 조회 결과를 그대로 담아두는 **캐시**일 뿐이고, 진짜 원본은
    `reflex.db` 파일 안에 있다.
    """

    fruits: list[dict] = []

    new_fruit_name: str = ""
    form_error: str = ""

    @rx.event
    def load_fruits(self):
        """DB에서 과일 목록을 읽어와 `self.fruits`에 채운다.

        페이지의 `on_load`에 연결해서, 그 페이지가 열릴 때마다(=브라우저가
        접속할 때마다) 최신 DB 상태를 다시 읽어오도록 한다.
        """
        with rx.session() as session:
            records = session.exec(sqlmodel.select(FruitRecord)).all()
            if not records:
                # 최초 실행(테이블은 있지만 비어있음): 시드 데이터를 넣는다.
                records = [FruitRecord(**seed) for seed in SEED_FRUITS]
                session.add_all(records)
                session.commit()
                for record in records:
                    session.refresh(record)
            self.fruits = [record.model_dump() for record in records]

    @rx.event
    def set_new_fruit_name(self, value: str):
        """입력창의 값이 바뀔 때마다 실행된다 (Controlled Component).

        Vue의 `v-model`, React의 `value + onChange` 조합과 같은 역할을
        하지만, 여기서는 값을 들고 있는 쪽이 브라우저가 아니라 **서버의
        State**라는 점이 다르다.
        """
        self.new_fruit_name = value
        self.form_error = ""

    @rx.event
    def add_fruit(self):
        """Create — 입력창의 이름으로 새 과일을 DB에 추가한다 (서버 측 검증 포함)."""
        name = self.new_fruit_name.strip()
        if not name:
            self.form_error = "이름을 입력하세요."
            return
        if len(name) > 10:
            self.form_error = "이름은 10자 이내로 입력하세요."
            return
        if any(f["name"] == name for f in self.fruits):
            self.form_error = f"'{name}'은(는) 이미 목록에 있습니다."
            return
        with rx.session() as session:
            session.add(FruitRecord(name=name, in_stock=True))
            session.commit()
        self.new_fruit_name = ""
        self.form_error = ""
        self.load_fruits()

    @rx.event
    def remove_fruit(self, fruit_id: int):
        """Delete — id가 일치하는 과일을 DB에서 제거한다."""
        with rx.session() as session:
            record = session.get(FruitRecord, fruit_id)
            if record is not None:
                session.delete(record)
                session.commit()
        self.load_fruits()

    @rx.event
    def toggle_stock(self, fruit_id: int):
        """id가 일치하는 과일의 재고 여부를 DB에서 직접 뒤집는다.

        study2~6에서는 `self.fruits` 리스트를 직접 수정하는 것만으로
        충분했지만, 이제 `self.fruits`는 DB의 캐시일 뿐이므로 **원본(DB
        row)을 먼저 바꾸고, 그 다음 `load_fruits()`로 캐시를 새로
        고친다.**
        """
        with rx.session() as session:
            record = session.get(FruitRecord, fruit_id)
            if record is not None:
                record.in_stock = not record.in_stock
                session.add(record)
                session.commit()
        self.load_fruits()

    # --- study6: 별도로 떠 있는 FastAPI(외부 API) 연동 ---
    fruit_fact: str = ""
    fruit_fact_loading: bool = False

    @rx.event
    async def load_fruit_fact(self):
        """`external_api/`(별도 FastAPI 프로세스, 8001번 포트)에 HTTP 요청을
        보내 지금 보고 있는 과일의 잡학 정보를 가져온다.

        `async def` + 중간에 `yield`를 쓰면, 그 시점까지 바뀐 State를
        먼저 브라우저로 보내고(로딩중 표시) 나머지 코드를 계속 실행할 수
        있다. axios/fetch 요청 중 "로딩 스피너"를 보여주던 패턴과 목적이
        같다.
        """
        self.fruit_fact_loading = True
        self.fruit_fact = ""
        yield  # 여기까지의 상태(로딩중)를 먼저 브라우저에 반영

        name = self.current_fruit["name"]
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{EXTERNAL_API_BASE_URL}/api/fruit-fact/{name}", timeout=5
                )
                response.raise_for_status()
                self.fruit_fact = response.json()["fact"]
        except httpx.HTTPError:
            self.fruit_fact = (
                "정보를 가져오지 못했습니다. "
                "external_api 서버(8001번 포트)가 실행 중인지 확인하세요."
            )
        finally:
            self.fruit_fact_loading = False

    # --- study8: 로그인 상태 관리 (보호된 페이지) ---
    username_input: str = ""
    password_input: str = ""
    login_error: str = ""
    is_logged_in: bool = False
    current_username: str = ""

    @rx.event
    def set_username_input(self, value: str):
        self.username_input = value
        self.login_error = ""

    @rx.event
    def set_password_input(self, value: str):
        self.password_input = value
        self.login_error = ""

    @rx.event
    def login(self):
        """아이디/비밀번호를 확인하고, 맞으면 `/admin`으로 이동시킨다."""
        username = self.username_input.strip()
        if DEMO_USERS.get(username) != self.password_input:
            self.login_error = "아이디 또는 비밀번호가 올바르지 않습니다."
            return
        self.is_logged_in = True
        self.current_username = username
        self.password_input = ""
        return rx.redirect("/admin")

    @rx.event
    def logout(self):
        self.is_logged_in = False
        self.current_username = ""
        return rx.redirect("/login")

    @rx.event
    def require_login(self):
        """보호된 페이지의 `on_load`에 연결하는 이벤트 핸들러.

        로그인이 안 되어 있으면 `/login`으로 돌려보낸다. Vue Router의
        네비게이션 가드, React Router의 Protected Route와 같은 역할을
        "페이지 진입 시 실행되는 이벤트 핸들러 안의 `return rx.redirect(...)`"
        로 구현한 것이다.
        """
        if not self.is_logged_in:
            return rx.redirect("/login")

    @rx.var
    def current_fruit(self) -> dict:
        """동적 라우트 `/fruit/[fruit_id]`에서 쓰는 파생 값.

        `self.fruit_id`는 우리가 선언한 적 없는 속성이다. Reflex가
        `app.add_page(fruit_detail, route="/fruit/[fruit_id]")`로 페이지를
        등록할 때, 대괄호 세그먼트 이름과 같은 이름의 문자열 속성을
        State에 자동으로 만들어준다 (Vue Router/React Router의 라우트
        파라미터와 같은 개념 — Reflex는 이걸 URL 파라미터가 아니라
        "State 속성"으로 노출한다).
        """
        for fruit in self.fruits:
            if str(fruit["id"]) == self.fruit_id:
                return fruit
        return {"id": 0, "name": "", "in_stock": False}

    @rx.var
    def in_stock_count(self) -> int:
        """파생 값(ComputedVar). Vue의 computed, React의 파생 state에 대응한다.

        이 메서드 본문은 서버(Python)에서 실행되므로 평범한 리스트
        컴프리헨션을 그대로 써도 된다 — rx.cond/rx.foreach가 필요한 건
        "컴포넌트 함수" 쪽이지, State 내부 로직이 아니다.
        """
        return len([f for f in self.fruits if f["in_stock"]])
