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
