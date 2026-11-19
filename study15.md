# study15 — 단위·통합·E2E 테스트와 CI

목표: 브라우저→이벤트→DB→화면을 테스트하고 CI 성공 이후에만 배포한다.

실제 구현: [tests/](tests/), [.github/workflows/ci.yml](.github/workflows/ci.yml). 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

단위 테스트는 입력 규칙, DB 통합 테스트는 권한·트랜잭션·동시성, E2E는 실제 브라우저 이벤트를 검증한다. HTTP 200만으로 이벤트 성공을 판단하지 않는다.

[tests/](tests/), [브라우저 테스트](tests/e2e/test_browser.py), [격리 실행 도구](tools/verify_app.py), [실제 CI](.github/workflows/ci.yml)가 구현되어 있다. 전체 명령은 저장소 루트에서 실행한다.

## 🛠️ 실기(코드·줄별 설명)

실제 DB 권한 회귀 테스트 발췌다. `accounts` fixture는 임시 DB에 해시 계정과 토큰을 준비하며 [conftest.py](tests/conftest.py)에 있다.
```python
def make_post(raw):
    with open_session() as session:
        return posts.create_post(session, raw, PAYLOAD)

@pytest.mark.parametrize("anonymous", [True, False])
def test_denied_changes_keep_database(accounts, anonymous):
    owner, other = accounts
    post_id = make_post(owner)
    token = "" if anonymous else other
    with open_session() as session:
        with pytest.raises(AccessDenied):
            posts.update_post(session, token, post_id, PostInput(title="침해", content="침해"), 1)
    with open_session() as session:
        with pytest.raises(AccessDenied):
            posts.delete_post(session, token, post_id)
    with open_session() as session:
        assert posts.read_post(session, post_id).title == "원래 제목"

def test_owner_crud_and_conflict(accounts):
    owner, _ = accounts
    post_id = make_post(owner)
    with open_session() as session:
        row = posts.read_post(session, post_id)
        assert row.owner_id is not None and row.author == "demo"
        posts.update_post(
            session, owner, post_id, PostInput(title="새 제목", content="새 본문"), row.revision
        )
    with open_session() as session:
        assert posts.read_post(session, post_id).revision == 2
        with pytest.raises(Conflict):
            posts.update_post(session, owner, post_id, PAYLOAD, 1)
    with open_session() as session:
        posts.delete_post(session, owner, post_id)
    with open_session() as session:
        assert session.get(Post, post_id) is None
```

- `make_post`는 실제 서비스로 소유자 글을 만든다.
- 두 매개변수는 비로그인과 타인을 각각 시험한다.
- 수정·삭제는 둘 다 거부되어야 하며 새 DB 세션에서 원래 제목을 확인한다.
- 소유자 수정은 revision을 1 증가시킨다. 이전 revision으로 재수정하면 Conflict가 나야 한다.
- 삭제 뒤 DB 행이 없음을 별도 세션에서 검사한다.

```powershell
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python -m pytest tests --ignore=tests/e2e -q
python tools/verify_app.py --app demo --mode prod
python tools/verify_app.py --app midpoint --mode prod
python tools/verify_app.py --app project --mode prod
```

`verify_app.py`는 임시 DB→migration→필요한 로컬 계정→별도 포트 서버→Chromium→프로세스 정리 순서다. 실제 DB와 API 키를 사용하지 않는다. `--mode prod`는 export와 단일 포트 실행까지 포함한다. 실행 로그·스크린샷은 `artifacts/`에 저장한다.

실제 CI 구성:

```yaml
name: reflex-study-ci
on: [push, pull_request]
permissions:
  contents: read
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m venv .venv
      - run: printf '%s\n' "$GITHUB_WORKSPACE/.venv/bin" >> "$GITHUB_PATH"
      - run: python -m pip install --require-hashes -r requirements-dev.lock
      - run: python -m ruff check .
      - run: python -m ruff format --check .
      - run: pyright
      - run: python -m pytest tests --ignore=tests/e2e -q
      - run: python tools/benchmark.py
      - run: python tools/check_deploy.py
      - uses: actions/upload-artifact@v4
        with:
          name: benchmark
          path: artifacts/benchmark.json
  browser:
    needs: quality
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app: [demo, midpoint, project]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m venv .venv
      - run: printf '%s\n' "$GITHUB_WORKSPACE/.venv/bin" >> "$GITHUB_PATH"
      - run: python -m pip install --require-hashes -r requirements-dev.lock
      - run: python -m playwright install --with-deps chromium
      - run: python tools/verify_app.py --app ${{ matrix.app }} --mode prod
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: browser-${{ matrix.app }}
          path: |
            artifacts/
            test-results/
  deploy:
    needs: browser
    if: github.ref == 'refs/heads/main' && github.event_name == 'push' && vars.DEPLOY_ENABLED == 'true'
    environment: production
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    env:
      REGISTRY_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      SSH_KEY: ${{ secrets.DEPLOY_SSH_KEY }}
      SSH_KNOWN_HOSTS: ${{ secrets.DEPLOY_KNOWN_HOSTS }}
      DEPLOY_TARGET: ${{ secrets.DEPLOY_TARGET }}
      APP_DOMAIN: ${{ vars.APP_DOMAIN }}
    steps:
      - uses: actions/checkout@v4
      - name: Publish verified image and deploy
        shell: bash
        run: |
          set -euo pipefail
          repo=$(printf '%s' "$GITHUB_REPOSITORY" | tr '[:upper:]' '[:lower:]')
          image="ghcr.io/${repo}:${GITHUB_SHA}"
          test -n "$APP_DOMAIN"
          printf '%s' "$REGISTRY_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin
          docker build --build-arg "PUBLIC_API_URL=https://${APP_DOMAIN}" -t "$image" project
          docker push "$image"
          mkdir -p ~/.ssh
          chmod 700 ~/.ssh
          key_file=$(mktemp)
          trap 'rm -f "$key_file"' EXIT
          printf '%s\n' "$SSH_KEY" > "$key_file"
          chmod 600 "$key_file"
          printf '%s\n' "$SSH_KNOWN_HOSTS" > ~/.ssh/known_hosts
          ssh -i "$key_file" -o StrictHostKeyChecking=yes "$DEPLOY_TARGET" "/srv/reflex/deploy.sh '$image'"
```

- `quality`는 고정된 Linux 개발 lock으로 설치하고 린트·포맷·타입·단위/DB·성능 검사를 한다.
- `browser`는 세 앱의 prod 빌드와 브라우저 흐름을 matrix로 검증한다.
- `deploy`는 matrix 성공, main push, `DEPLOY_ENABLED=true`를 모두 요구한다.
- production 비밀 값은 해당 job에서만 주입한다. SSH 호스트 키를 사전에 확인하고 이미지에 SHA 태그를 붙인다.
- 이 워크플로 파일의 구현과 GitHub 원격 실행 성공은 구분한다. 원격 실행은 저장소에 반영된 뒤 확인해야 한다.

## 오류 노트

- `REFLEX_E2E_URL` 없이 직접 E2E를 실행하면 의도적으로 건너뛴다. 격리 실행 도구를 사용한다.
- 첫 실패 경계를 수정한 뒤 다시 검증한다. 임의 sleep보다 Playwright assertion으로 UI 반영을 기다린다.
- 테스트 실패 로그에도 비밀번호·토큰·AI 입력을 출력하지 않는다.

## ☐ 체크리스트

- ☐ 단위·DB·E2E가 보장하는 경계를 설명한다.
- ☐ [노션 권한 검사] 타인·만료 세션의 DB 불변성을 확인한다.
- ☐ 로그인 제한·AI 한도를 경쟁 요청으로 시험한다.
- ☐ 실제 read-only MCP 왕복과 mock AI 응답을 구분한다.
- ☐ CI 성공 이후에만 게시·배포 job이 실행되도록 확인한다.

## 다음 단계 연결

[study16](study16.md)에서 운영 인증·로그·복원 절차를 확인한다.
