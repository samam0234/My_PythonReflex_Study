# study14 — Python 타입·스키마·정적 분석

목표: 실제 Reflex 입력·화면 DTO에 타입과 엄격한 검증을 적용한다.

실제 구현: [project/project/schemas.py](project/project/schemas.py), [pyproject.toml](pyproject.toml). 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

구현 언어가 Python이므로 Python 타입·Pydantic·Ruff·Pyright를 사용한다. 정적 타입은 외부 입력 검증을 대신하지 않는다. `PostInput`은 추가 필드와 비문자열을 거절하고 `PostSummary`는 목록에 필요한 정보만 공개한다.

구현 파일은 [schemas.py](project/project/schemas.py), [pyproject.toml](pyproject.toml)이다.

## 🛠️ 실기(코드·줄별 설명)

```python
"""study5·14: 외부 입력을 엄격히 검사하고 화면 DTO를 별도로 정의."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Body = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
Username = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[a-z][a-z0-9_]{2,31}$")
]


class PostInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    title: Title
    content: Body


class LoginInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    username: Username
    password: str = Field(min_length=12, max_length=128)


class PostSummary(BaseModel):
    id: int
    title: str
    author: str
    created_at: str


class PostDetail(PostSummary):
    content: str
    owner_id: int | None = None
    revision: int = 1


class PostPage(BaseModel):
    items: list[PostSummary]
    total: int
    page: int


def parse_post_id(raw: str | int) -> int:
    text = str(raw)
    if not text.isascii() or not text.isdecimal() or len(text) > 10:
        raise ValueError("올바른 글 번호가 아닙니다.")
    value = int(text)
    if not 1 <= value <= 2_147_483_647:
        raise ValueError("올바른 글 번호가 아닙니다.")
    return value
```

- `Annotated`, `StringConstraints`는 공백 제거·필수·길이를 정의한다.
- `PostInput`의 strict·extra 설정은 숫자 강제 변환과 작성자/owner ID 주입을 거부한다.
- `LoginInput`은 계정 이름 규칙과 12~128자 비밀번호를 검증한다.
- `PostSummary`에는 본문이 없고 `PostDetail`에만 본문·revision을 둔다.
- `PostPage`는 페이지 데이터·개수·위치를 묶는다.
- `parse_post_id`는 ASCII 숫자·길이·양수 범위를 검사한다.

실제 정적 분석 설정:

```toml
[tool.ruff]
target-version = "py312"
line-length = 100
extend-exclude = [".web", ".venv", "reflex.lock", "alembic/versions"]

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "I"]

[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "basic"
include = ["project/project/schemas.py", "project/project/services", "project/project/settings.py"]
extraPaths = ["project"]
venvPath = "."
venv = ".venv"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["project", "midpoint", "demo"]
asyncio_mode = "auto"
markers = ["e2e: 실행 중인 Reflex 서버를 검증하는 브라우저 테스트"]
```

Ruff는 오류성 패턴과 import를 검사하고 포매터는 모양을 통일한다. Pyright는 순수 스키마·설정·서비스를 검사한다. 동적 State·UI는 prod export와 E2E로 추가 검증한다. SQLModel 클래스 필드는 쿼리에서 `col(Post.id)`처럼 사용해 정적 분석에도 SQL 표현식임을 알린다.

```powershell
python -m ruff check .
python -m ruff format --check .
pyright
python -m pytest tests/test_validation.py -q
```

명령은 저장소 루트 기준이다. 코드의 의도까지 검증하는 테스트와 형식·타입 검사를 따로 확인한다.

## 오류 노트

- Var·동적 라우트를 `Any`로 전부 덮지 않는다. 입력 경계와 서비스부터 타입을 좁힌다.
- 예외의 Pydantic 원문에는 입력이 포함될 수 있다. UI에는 정해진 일반 문구를 표시한다.
- 생성된 `.web/` 파일의 타입·코드를 직접 수정하지 않는다.

## ☐ 체크리스트

- ☐ 엄격한 스키마가 공백·경계값·비문자열·추가 필드를 거부한다.
- ☐ [노션 직렬화 메모] ORM·datetime과 공개 DTO를 분리한다.
- ☐ State·이벤트·computed 반환 타입을 확인한다.
- ☐ Ruff·포맷·Pyright와 브라우저 검증의 범위를 구분한다.

## 다음 단계 연결

[study15](study15.md)에서 이 검사들을 실제 CI에 연결한다.
