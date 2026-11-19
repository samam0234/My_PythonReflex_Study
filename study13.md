# study13 — UI·유틸 라이브러리 연동

목표: Reflex 내장 UI·차트와 Python 유틸을 사용해 게시판의 필터·통계를 만든다.

실제 구현: [demo/demo/lessons/charts.py](demo/demo/lessons/charts.py), [project/project/utils/dates.py](project/project/utils/dates.py). `demo/`에서 실행 후 `/study13`로 접속한다. 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

먼저 Reflex가 제공하는 UI 래퍼를 사용한다. Radix 기반 입력·선택·테마, `rx.recharts` 차트는 Python 컴포넌트로 사용할 수 있다. 설치 수나 인기 순위를 단정하는 대신 이 코스에 필요한 기능과 유지 비용으로 선택한다.

Python 유틸은 서버에서 데이터를 가공하고, UI는 직렬화 가능한 결과만 받는다. 예를 들어 UTC 날짜를 지역 시간으로 표시하거나 게시글 수를 집계할 수 있다. 차트용 전체 원본을 브라우저에 보내지 말고 집계 결과만 전달한다.

## 🛠️ 실기(코드·줄별 설명)

독립 실습 진입점 전체 예제다. 실제 게시판에서는 고정 `DATA`를 DB 집계 결과로 바꾼다.

```python
import reflex as rx

DATA = [
    {"day": "월", "count": 3},
    {"day": "화", "count": 5},
    {"day": "수", "count": 2},
]

class ChartState(rx.State):
    period: str = "최근 3일"

    @rx.event
    def set_period(self, value: str):
        if value in {"최근 3일", "오늘"}:
            self.period = value

    @rx.var
    def chart_data(self) -> list[dict[str, str | int]]:
        return DATA[-1:] if self.period == "오늘" else DATA

def index() -> rx.Component:
    return rx.vstack(
        rx.select(["최근 3일", "오늘"], value=ChartState.period, on_change=ChartState.set_period),
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
            rx.recharts.x_axis(data_key="day"),
            rx.recharts.y_axis(),
            rx.recharts.tooltip(),
            rx.recharts.bar(data_key="count", fill="#4f46e5"),
            data=ChartState.chart_data,
            width="100%",
            height=260,
        ),
        width="100%",
        max_width="640px",
    )

app = rx.App()
app.add_page(index)
```

| 코드 | 줄별 설명 |
|---|---|
| `DATA` 세 행 | 외부 요청 없는 집계 샘플이다. |
| `period` | 선택된 필터를 저장한다. |
| `set_period` / 허용 목록 | 클라이언트 값을 검증한 뒤 상태를 변경한다. |
| `chart_data` | 실제 서버 값에 Python 조건문을 적용해 데이터 범위를 고른다. |
| `rx.select` | 필터 값과 이벤트를 명시적으로 연결한다. |
| `cartesian_grid` | 점선 보조 격자를 표시한다. |
| `x_axis`, `y_axis` | 범주 키와 수치 축을 지정한다. |
| `tooltip`, `bar` | 마우스 안내와 막대 시리즈를 만든다. |
| `data`, `width`, `height` | 차트 데이터와 필수 표시 영역을 지정한다. |
| `max_width` | 데스크톱에서 과도한 확장을 제한한다. |
| `App`, `add_page` | 앱과 페이지를 등록한다. 테마는 `rxconfig.py`의 RadixThemesPlugin에서 설정한다. |

Python 날짜 유틸 `project/utils/dates.py`에 둘 함수 예제:

```python
from datetime import datetime
from zoneinfo import ZoneInfo

def seoul_time(iso_utc: str) -> str:
    value = datetime.fromisoformat(iso_utc)
    if value.tzinfo is None:
        raise ValueError("UTC offset이 필요합니다.")
    return value.astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M")
```

import 두 줄은 날짜 파싱과 시간대 데이터를 사용한다. `fromisoformat`은 문자열을 날짜로 만들고, `tzinfo` 검사는 출처가 모호한 naive 날짜를 거부한다. 마지막 줄은 서울 시간으로 변환해 표시한다. Windows·슬림 이미지에서 시간대 DB가 없으면 `python -m pip install tzdata`를 설치한다.

실행 후 필터를 바꾸면 막대가 세 개에서 한 개가 되어야 한다. 차트 대신 접근 가능한 텍스트 요약도 제공하고 키보드로 select를 조작한다. study12와 같은 방식으로 차트 도입 전후 초기 JS 전송량을 기록한다.

## 오류 노트

- 차트가 비어 있으면 높이·부모 폭·data_key 오타·숫자 값 타입을 확인한다.
- 최신 문서의 UI 속성이 고정 버전에 없으면 0.9.11 설치 API와 공식 버전 이력을 확인한다.
- 앱을 위해 별도 프론트 프로젝트를 만들거나 생성된 `.web/`를 수정하지 않는다.
- 날짜에 시간대가 없는데 로컬 시간으로 임의 추정하면 배포 환경마다 달라진다.

## ☐ 체크리스트

- ☐ [노션 설정 예제] Radix UI·테마와 기존 Tailwind 플러그인의 역할을 설명한다.
- ☐ select 이벤트에 명시적 setter와 허용 값 검증을 둔다.
- ☐ 차트·텍스트 요약·키보드 조작을 확인한다.
- ☐ UTC 저장과 서울 시간 표시를 구분한다.
- ☐ [study12 측정](study12.md)에서 목록과 대시보드의 실제 JS 전송량을 비교하고 차트만의 비용을 분리하려면 어떤 조건을 고정해야 할지 적는다.

## 다음 단계 연결

[study14](study14.md)에서 화면 데이터와 입력의 타입을 명확히 하고 정적 분석을 적용한다.

참고: [공식 막대 차트](https://reflex.dev/docs/library/graphing/charts/barchart/), [select 컴포넌트 소스 문서](https://github.com/reflex-dev/reflex/blob/main/docs/library/forms/select.md).
