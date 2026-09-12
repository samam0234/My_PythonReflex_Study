"""study6 실습용 '외부' 백엔드.

Reflex 앱과는 완전히 별개의 FastAPI 프로세스로 실행한다. 회사에서 이미
운영 중인 FastAPI/Django API가 있고, 그 API를 Reflex 이벤트 핸들러에서
호출하는 상황을 흉내 낸 것이다.

실행: uvicorn external_api.main:app --port 8001
"""

from fastapi import FastAPI

app = FastAPI()

FRUIT_FACTS = {
    "사과": "사과는 장미과 식물로, 배와 가까운 친척이다.",
    "바나나": "바나나는 식물학적으로 열매가 아니라 '베리(berry)'로 분류된다.",
    "포도": "포도씨에는 항산화 성분(폴리페놀)이 풍부하다.",
}


@app.get("/api/fruit-fact/{name}")
def get_fruit_fact(name: str) -> dict:
    fact = FRUIT_FACTS.get(name, f"'{name}'에 대한 정보가 아직 등록되지 않았습니다.")
    return {"name": name, "fact": fact}
