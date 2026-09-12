import httpx
import reflex as rx

EXTERNAL_API_BASE_URL = "http://127.0.0.1:8001"


class State(rx.State):
    """앱 전역 상태. study1의 고정 Python 리스트가 이제 이 클래스 안으로 들어와
    진짜 "상태"가 된다 — 값이 바뀌면 화면이 자동으로 다시 그려진다.
    """

    fruits: list[dict] = [
        {"id": 1, "name": "사과", "in_stock": True},
        {"id": 2, "name": "바나나", "in_stock": False},
        {"id": 3, "name": "포도", "in_stock": True},
    ]

    new_fruit_name: str = ""
    form_error: str = ""

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
        """Create — 입력창의 이름으로 새 과일을 추가한다 (서버 측 검증 포함)."""
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
        next_id = max((f["id"] for f in self.fruits), default=0) + 1
        self.fruits.append({"id": next_id, "name": name, "in_stock": True})
        self.new_fruit_name = ""
        self.form_error = ""

    @rx.event
    def remove_fruit(self, fruit_id: int):
        """Delete — id가 일치하는 과일을 목록에서 제거한다."""
        self.fruits = [f for f in self.fruits if f["id"] != fruit_id]

    @rx.event
    def toggle_stock(self, fruit_id: int):
        """id가 일치하는 과일의 재고 여부를 뒤집는다.

        self.fruits는 State가 감시하는 리스트이므로, 그 안의 dict 항목을
        직접 수정(`fruit["in_stock"] = ...`)해도 Reflex가 변경을 감지해
        브라우저에 새 값을 보내준다. (Vue의 반응형 배열/객체와 동일한 감각)
        """
        for fruit in self.fruits:
            if fruit["id"] == fruit_id:
                fruit["in_stock"] = not fruit["in_stock"]

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
