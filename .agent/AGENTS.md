# 에이전트 공통 가이드

## 저장소와 현재 요청

Python Reflex 0.9.11 학습 과정이다. 사용자가 지정한 새 순서의 `study0.md`~`study18.md`, `studyMidpoint.md`, `studyFinal.md`가 기준이다. 기본 과정은 Reflex 단독으로 유지한다. 사용자가 승인한 두 확장 과제는 study4의 Vue·React 비교와 study6의 FastAPI 게시판 HTTP 연동이다. 과거 코드 주석의 단원 번호보다 루트 문서를 우선한다.

- `demo/`: 독립된 Reflex 단원별 화면. study1~7, study11, study13의 실행 예제.
- `backend/`: 독립 FastAPI 게시판과 과일 API. Reflex 연결 명령은 해당 README에 있다.
- `midpoint/`: study0~10 기능만 쓰는 데모 로그인 게시판.
- `project/`: study11~18을 연결한 최종 게시판. DB 사용자·만료 세션·소유권·페이지네이션·AI·MCP.
- `tests/`: 단위·DB·비동기·migration·브라우저 테스트.
- `tools/`: 성능 측정·실행 검증 도구.
- 루트 `.venv/`는 검증 환경이며 커밋하지 않는다. 각 앱은 자체 requirements로 설치할 수 있다.

## 작업 규칙

1. 관련 study 문서와 구현·테스트를 함께 확인한다. 문서와 코드 경로를 일치시킨다.
2. 코드·문서·커밋 설명은 한글, 식별자·파일명·커밋 prefix는 영어를 사용한다.
3. Windows PowerShell에서 Python으로 한글을 파이프할 때 `$OutputEncoding = [System.Text.UTF8Encoding]::new()`와 `python -X utf8`를 사용한다. 또는 UTF-8을 보존하는 패치 도구를 쓴다.
4. 기존 DB를 시험용으로 변경하지 않는다. 테스트·빌드는 명시적인 임시 DB URL을 사용한다.
5. 실제 API 키·세션 토큰·비밀번호·DB 파일·생성 `.web/`는 커밋하지 않는다.
6. 인증 근거는 backend State 토큰과 DB 세션이다. 공개 이름·화면 버튼을 권한 근거로 삼지 않는다.
7. 코드 구현·로컬 검증·외부 배포·실제 유료 API 호출을 구분해 기록한다. 실행하지 않은 검사는 성공으로 표시하지 않는다.
8. 커밋 요청이 있으면 [COMMIT_GUIDE.md](COMMIT_GUIDE.md)를 따른다. 요청 없이 커밋·푸시하지 않는다.
9. 노션은 사용자 요청 범위에서 코드·검증 후에 갱신하고 관련 없는 기존 기록은 보존한다.

## 인수인계

구현 경로·실행 명령·현재 검증 결과는 루트 README와 studyFinal에 기록한다. 실제 외부 배포는 운영 계정·도메인·비밀 값이 준비된 뒤 해당 절차를 따르며, 예제 주소를 배포 완료로 간주하지 않는다.
