# study10 — 프로덕션 빌드·배포·기초 총정리

목표: 기초 게시판을 prod로 빌드·실행하고 study0~10의 상태·데이터·권한 흐름을 설명한다.

실제 구현: [midpoint/](midpoint/), [격리 검증 도구](tools/verify_app.py). 설치는 [README](README.md)를 따른다.

## 📖 이론

개발 서버와 prod 빌드는 별도 확인 사항이다. 프론트 자산·상시 Python 백엔드·WebSocket·영속 DB가 필요하다. Reflex 0.9.11 prod는 한 포트로 함께 제공할 수 있다. 정적 파일 업로드만으로 State 이벤트가 동작하지는 않는다.

이 단원은 기초 기능만 쓰는 `midpoint/`를 대상으로 한다. 외부 서비스에 배포할 코드는 study17의 `project/` Docker·Compose로 심화한다. 학습용 데모 인증을 그대로 운영 계정으로 사용하지 않는다.

## 🛠️ 실기(코드·줄별 설명)

저장소 루트에서 기초 테스트와 실제 prod 브라우저를 검증한다.

```powershell
python -m pytest tests/test_midpoint_validation.py -q
python tools/verify_app.py --app midpoint --mode prod
```

첫 줄은 필수·공백·길이 경계를 검사한다. 둘째 줄은 임시 DB migration→prod export→단일 포트 실행→브라우저 로그인·CRUD·권한 검사를 수행하고 서버를 정리한다. 기존 DB와 키를 사용하지 않는다.

명령을 직접 따라 실행할 때:

```powershell
cd midpoint
python -m pip install -r requirements.txt
reflex db migrate
$env:REFLEX_API_URL = "http://localhost:3000"
reflex export --frontend-only --no-zip --env prod
reflex run --env prod --single-port --frontend-port 3000 --backend-host 127.0.0.1
```

1. `cd`는 기초 앱의 설정·패키지를 선택한다.
2. pip는 고정된 기본 런타임·DB extra를 설치한다.
3. migrate는 기존 Alembic 이력을 적용한다. 이미 있는 이력을 재초기화하지 않는다.
4. API URL은 prod 단일 포트에 맞춘다. 개발 기본 8000과 구분한다.
5. export는 ZIP 없이 프로덕션 프론트 자산을 만든다.
6. run은 같은 포트에서 자산·이벤트를 제공한다. `http://localhost:3000`에서 실제 로그인·CRUD를 확인한다.

Reflex Cloud를 선택하면 대시보드에서 프로젝트를 만들고 [공식 배포 안내](https://reflex.dev/docs/hosting/deploy-quick-start/)의 프로젝트별 명령·비밀 값·영속 DB 설정을 따른다. 이 과정에서 실제 Cloud 계정이나 배포 URL을 생성하지 않았다.

기초 복습 문제:

1. 컴포넌트의 `State.posts`에 Python for를 직접 쓸 수 없는 이유는?
2. `self.posts.append`와 DB `session.add`의 저장 수명은 어떻게 다른가?
3. 수정 버튼을 숨긴 뒤에도 이벤트에서 작성자 검사가 필요한 이유는?
4. 외부 화면의 API 주소가 localhost라면 어느 컴퓨터를 가리키는가?
5. migration 생성과 적용은 각각 언제 하는가?

해설: 1은 Var와 실제 값의 실행 시점 차이, 2는 화면 상태와 영속 DB의 차이, 3은 UI 우회 가능성, 4는 사용자 브라우저의 컴퓨터, 5는 개발 중 이력 작성·검토 후 배포 시 적용이다. 해당 코드 줄을 찾아 함께 설명한다.

## 오류 노트

- HTTP 200만 보지 말고 실제 이벤트·DB 변경·화면 결과를 확인한다.
- 단일 포트에 서로 다른 frontend/backend 포트를 명시하면 CLI가 거부한다.
- `REFLEX_CORS_ALLOWED_ORIGINS`는 쉼표 구분 문자열이다. JSON 배열로 주입하지 않는다.
- API URL을 바꾸면 프론트도 재빌드한다. HTTPS 화면과 HTTP API를 섞지 않는다.
- Docker 파일시스템은 영속 볼륨과 다르다. 저장·재시작·복원을 각각 확인한다.

## ☐ 체크리스트

- ☐ [노션 학습 목표] Docker 또는 Reflex Cloud 배포 경로와 필요한 자산을 설명한다.
- ☐ [노션 제약] 프론트·상시 백엔드·WebSocket·영속 DB의 책임을 설명한다.
- ☐ prod export·단일 포트·실제 로그인 CRUD와 권한을 확인한다.
- ☐ 학습용 로그인과 운영 DB 계정을 구분한다.
- ☐ 복습 다섯 문제를 코드 위치와 함께 설명한다.
- ☐ 외부 계정 배포는 실제 URL·로그로 별도 검증한다.

## 다음 단계 연결

[studyMidpoint](studyMidpoint.md)에서 기초 기능을 종합한 게시판의 폴더·구현 순서·완성 점검·회고를 확인한다.
