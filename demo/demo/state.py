import reflex as rx


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

    @rx.var
    def in_stock_count(self) -> int:
        """파생 값(ComputedVar). Vue의 computed, React의 파생 state에 대응한다.

        이 메서드 본문은 서버(Python)에서 실행되므로 평범한 리스트
        컴프리헨션을 그대로 써도 된다 — rx.cond/rx.foreach가 필요한 건
        "컴포넌트 함수" 쪽이지, State 내부 로직이 아니다.
        """
        return len([f for f in self.fruits if f["in_stock"]])
