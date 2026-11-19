# study9 — 테스트·디버깅의 기초

목표: 검증 함수의 경계값을 테스트하고 UI·이벤트·DB 오류를 구분해 조사한다.

실제 구현: [tests/test_midpoint_validation.py](tests/test_midpoint_validation.py), [tests/e2e/test_browser.py](tests/e2e/test_browser.py). 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

단위 테스트는 순수 검증 함수를, DB 테스트는 저장과 권한 처리를, 브라우저 검증은 실제 페이지·WebSocket 이벤트를 확인한다. HTTP 200만으로 클릭·로그인·CRUD 성공을 판단하지 않는다.

Reflex에서는 Python traceback과 브라우저 콘솔을 같이 봐야 한다. 컴포넌트 생성 단계 오류인지, 서버 이벤트 실행 오류인지, WebSocket 연결 오류인지 먼저 분류한다. 운영 DB와 테스트 DB는 분리한다.

## 🛠️ 실기(코드·줄별 설명)

기초 게시판의 `midpoint/midpoint/validation.py`에 순수 검증 함수를 구현했다. 이 함수는 UI import 없이 테스트한다.

`tests/test_midpoint_validation.py`:

```python
import pytest
from midpoint.validation import validate_post

@pytest.mark.parametrize("title,content,valid", [
    ("제목", "본문", True),
    (" ", "본문", False),
    ("가" * 50, "본문", True),
    ("가" * 51, "본문", False),
    ("제목", " ", False),
    ("제목", "가" * 5000, True),
    ("제목", "가" * 5001, False),
])
def test_validate_post(title: str, content: str, valid: bool):
    assert (validate_post(title, content) == "") is valid
```

- `pytest`는 테스트 실행·매개변수화를 제공한다.
- import는 화면을 실행하지 않고 검증 함수만 가져온다.
- `parametrize`는 입력 두 개와 기대 성공 여부를 각 테스트로 확장한다.
- 일곱 행은 정상·공백·제목 경계·본문 경계를 확인한다.
- `assert`는 “오류 없음”과 기대 성공 여부가 같은지 비교한다.

```powershell
python -m pip install pytest
python -m pytest tests/test_midpoint_validation.py -q
reflex run --loglevel debug
```

첫 줄은 테스트 도구 설치, 둘째 줄은 테스트 실행, 셋째 줄은 이벤트 오류 조사에 필요한 개발 로그 출력이다. 디버그 로그는 로컬에서만 사용하고 비밀번호·토큰을 넣지 않는다.

수동 확인 기록:

| 동작 | 기대 결과 | 관찰 결과 |
|---|---|---|
| `/post/abc` 직접 접근 | 설명 가능한 오류, traceback 없음 | final prod E2E 통과 |
| 비로그인 작성 | 로그인으로 이동 | midpoint·final prod E2E 통과 |
| 타인 글 수정·삭제 | DB 변화 없음 | DB·prod E2E 통과 |
| 정상 작성·새로고침 | DB 행과 화면 일치 | prod E2E 통과 |
| 서버 컨테이너 교체 | 새 프로세스에서 글 유지·메모리 세션 초기화·재로그인 가능 | 로컬 Docker TLS 검사 통과 |

조사 순서는 재현 입력 저장 → 브라우저 Console/Network → 서버 traceback의 첫 앱 코드 줄 → DB URL·migration 상태 → 최소 재현이다. 한 번에 여러 설정을 바꾸지 않는다.

## 오류 노트

| 오류 | 우선 확인 |
|---|---|
| Var bool 변환 | 컴포넌트 안 Python 제어문 사용 여부 |
| 동적 필드 접근 실패 | 라우트 등록·변수 이름 |
| 테이블 없음 | 실제 연결 DB·migration 적용 |
| WebSocket 반복 끊김 | API URL·포트·proxy upgrade·허용 origin |
| UnicodeEncodeError | study0의 두 UTF-8 환경변수 |

## ☐ 체크리스트

- ☐ 필수·공백·최대 길이 경계 테스트를 작성하고 결과를 기록한다.
- ☐ [노션 제약] Var 제어문 오류와 DB 영속성 문제를 재현·설명한다.
- ☐ 서버 traceback과 브라우저 WebSocket을 함께 확인한다.
- ☐ 테스트에 운영 DB·실제 비밀번호·유료 API를 사용하지 않는다.
- ☐ 미실행 항목을 성공으로 표시하지 않는다.

## 다음 단계 연결

[study10](study10.md)에서 테스트를 통과한 앱의 프로덕션 빌드·배포를 확인한다.

참고: [pytest 매개변수화](https://docs.pytest.org/en/stable/how-to/parametrize.html).
