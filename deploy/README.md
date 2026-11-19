# 외부 VM 배포

이 디렉터리의 파일을 Linux VM의 `/srv/reflex/`에 배치한다. Docker Compose와 GHCR 읽기 자격, 보유 도메인의 DNS, 외부 80/443 접근을 준비한다. 앱은 VM 한 대·인스턴스 하나·영속 SQLite를 기준으로 한다.

1. `.env.example`을 `.env`로 복사하고 `APP_IMAGE`(커밋 SHA 태그), `APP_DOMAIN`을 실제 값으로 설정한다.
2. `.env.runtime.example`을 `.env.runtime`으로 복사한다. AI를 쓰면 서버에서만 `OPENAI_API_KEY`, `AI_MODEL`을 설정한다. `chmod 600 .env .env.runtime`으로 읽기를 제한한다.
3. `chmod +x deploy.sh rollback.sh`를 실행한다.
4. 앱 이미지는 동일 도메인의 `PUBLIC_API_URL=https://실제도메인` 빌드 인자를 사용해야 한다.
5. `./deploy.sh ghcr.io/계정/저장소:40자리커밋SHA`를 실행한다. 이미지 내려받기 → 기존 DB 온라인 백업 → 앱 중지 → migration 1회 → readiness 성공 확인 순서다.
6. 외부에서 로그인·작성·새로고침·타인 권한 거부·WebSocket·로그아웃을 확인한다. 단일 인스턴스라 배포 중 짧은 중단이 있다.

마이그레이션 실패 시 새 버전을 시작하지 않는다. 백업은 영속 볼륨 `/data/backups/`에 있다. 백업을 별도 DB에 복원하여 `PRAGMA integrity_check`와 글·사용자 수를 검증하고, VM 외부에도 보관한다. 이미지 롤백은 DB 스키마 호환성을 확인한 뒤 `./rollback.sh 이전SHA이미지`로 수행한다. 파괴적인 스키마 변경은 이미지 교체만으로 복구되지 않는다.

GitHub Actions 배포는 production 환경에 `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS`, `DEPLOY_TARGET`을 등록하고 저장소 변수 `APP_DOMAIN`, `DEPLOY_ENABLED=true`를 설정하면 main push의 검증 성공 후 실행된다. 호스트 키는 사전에 확인한 값만 등록한다. GitHub 소스 파일을 VM에 자동 복사하지 않으므로 compose·배포 스크립트 변경도 함께 반영한다.

`python tools/check_deploy.py`는 자격증명·Docker daemon 없이 로컬에서 YAML·compose 해석·셸 문법·CI 의존성을 검사한다. Docker 이미지 실행, TLS 인증서 발급, GHCR 게시, SSH 배포는 외부 환경에서 별도 검증해야 한다.
