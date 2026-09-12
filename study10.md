# study10 (고급5) — Docker / Reflex Cloud 배포

study9에서 만든 프로덕션 빌드를 실제로 배포하는 두 가지 방법을 다룹니다: **직접 만든 Docker 이미지로 어디에나 배포하기**, 그리고 **Reflex 팀이 운영하는 Reflex Cloud에 한 줄로 배포하기**.

```
- [x] Reflex 프로젝트 생성과 실행
- [x] State 클래스로 화면 상태 관리
- [x] 이벤트 핸들러로 CRUD
- [x] 라우팅 / 페이지 분리
- [x] FastAPI 또는 Django API와 연동 가능성 확인
- [x] 배포 (도커 또는 Reflex 클라우드)
```

대응 실습: 신규 [`demo/Dockerfile`](./demo/Dockerfile), [`demo/docker-entrypoint.sh`](./demo/docker-entrypoint.sh), [`demo/.dockerignore`](./demo/.dockerignore)

> ⚠ 이 저장소를 작성한 환경에는 Docker 데몬이 떠 있지 않아 `docker build`를 실제로 실행해 검증하지는 못했습니다. 아래 Dockerfile은 study9까지 로컬에서 직접 검증한 명령(`reflex export`, `reflex run --env prod --single-port`)을 그대로 옮긴 것이지만, 실습할 때는 반드시 `docker build`/`docker run`으로 직접 확인하세요.

---

## 1. 핵심 발견: `--single-port`로 프론트+백엔드를 한 포트에

지금까지 `reflex run`은 프론트(3000)와 백엔드(8000)를 **서로 다른 포트**에 띄웠습니다. 컨테이너 하나로 간단히 배포하고 싶다면 이 두 포트를 합칠 수 있습니다.

```bash
reflex run --env prod --single-port --backend-host 0.0.0.0
```

- 프론트엔드(정적 파일 + 페이지)와 백엔드(API, WebSocket)가 **모두 하나의 포트**(기본 3000)에서 서빙됩니다. 컨테이너 하나에 포트 하나만 열면 되므로 배포가 단순해집니다.
- `--backend-host 0.0.0.0`: 컨테이너 밖에서 접속할 수 있도록 모든 인터페이스에 바인딩합니다 (기본값은 로컬호스트만 허용).

## 2. Reflex는 Node.js 대신 자체 런타임(Bun)을 쓴다

study0에서 "Reflex도 결국 Node.js가 필요하다"고 배웠는데, 정확히는 **Reflex가 자체적으로 Bun(Node 호환 JS 런타임)을 다운로드해서 사용**합니다. 그래서 Dockerfile의 베이스 이미지는 Python 이미지 하나면 충분하고, 별도로 Node.js를 설치할 필요가 없습니다 (Reflex가 처음 실행될 때 자동으로 받아옵니다).

## 3. Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 이미지 빌드 시점에 프론트엔드를 미리 컴파일해둔다.
RUN reflex export --frontend-only --no-zip --env prod

EXPOSE 3000

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
```

- `RUN reflex export ...`를 **빌드 시점**에 실행해서, 컨테이너가 뜰 때마다 프론트엔드를 다시 컴파일하지 않도록 합니다 (컨테이너 시작 속도 개선).
- DB 마이그레이션(`reflex db migrate`)은 빌드 시점이 아니라 **컨테이너 시작 시점**(entrypoint)에 실행합니다 — 이미지는 "코드"이고, DB는 "데이터"이므로 이미지를 빌드할 때 데이터베이스 파일을 구워 넣으면 안 됩니다.

```bash
# docker-entrypoint.sh
#!/bin/sh
set -e
reflex db migrate
exec reflex run --env prod --single-port --backend-host 0.0.0.0
```

## 4. 빌드 및 실행

```bash
cd demo
docker build -t reflex-demo .
docker run -p 3000:3000 --env-file .env reflex-demo
```

- `-p 3000:3000`: 컨테이너의 3000번(프론트+백엔드 통합 포트)을 호스트 3000번에 연결합니다.
- `--env-file .env`: study9에서 만든 `.env`(예: `REFLEX_DB_URL`, `EXTERNAL_API_BASE_URL`)를 컨테이너 안 환경변수로 그대로 전달합니다. **운영 DB는 컨테이너 안 SQLite 파일이 아니라, 컨테이너 밖의 관리형 DB(Postgres 등)를 `REFLEX_DB_URL`로 연결**하는 것이 정석입니다 — 컨테이너가 재시작되면 컨테이너 내부 파일 시스템의 SQLite 데이터는 사라지기 때문입니다 (볼륨 마운트로 유지할 수도 있지만, 여러 대로 확장하기 어렵습니다).
- 확인: `curl http://localhost:3000/ping` → 200 응답, 브라우저로 `http://localhost:3000` 접속 → study1~9의 모든 기능(과일 CRUD, 상세 페이지, 외부 API 호출, 로그인)이 그대로 동작하는지 확인합니다.

## 5. 대안 — Reflex Cloud

Docker/서버 운영 없이 빠르게 배포하고 싶다면, Reflex 팀이 운영하는 관리형 플랫폼에 배포할 수 있습니다.

```bash
reflex login     # 브라우저로 Reflex Cloud 계정 인증
reflex deploy --app-name my-fruit-demo
```

- `reflex deploy`는 내부적으로 `reflex export`와 비슷한 빌드 과정을 거친 뒤, 결과물을 Reflex Cloud(또는 연결된 GCP 계정, Enterprise 플랜)에 올립니다.
- `--env KEY=VALUE`(반복 가능)로 배포 환경의 환경변수를 지정할 수 있습니다 — study9에서 `.env`로 관리하던 값들을 그대로 옮기는 자리입니다.
- `--region`, `--vmtype`, `--min-instances`/`--max-instances`로 리전과 스펙, 오토스케일링을 지정합니다.
- 이 방식은 **계정 생성과 과금이 따르는 실제 배포 행위**이므로, 이 문서에서는 명령어만 소개하고 실제로 실행하지는 않았습니다. 실습해보고 싶다면 본인 계정으로 직접 `reflex login` 후 진행하세요.

## 6. Docker vs Reflex Cloud — 언제 무엇을

| | Docker(직접 배포) | Reflex Cloud |
|---|---|---|
| 인프라 제어 | 완전한 제어 (원하는 클라우드/온프레미스 어디든) | Reflex/연결된 GCP가 관리 |
| 설정 난이도 | Dockerfile, 리버스 프록시, DB 등 직접 구성 | `reflex deploy` 한 줄 |
| 비용 | 쓰는 인프라만큼 | Reflex Cloud 요금제 |
| 적합한 상황 | 기존 인프라(K8s, 사내 서버)에 맞춰야 할 때 | 빠른 데모/MVP, 인프라 관리 인력이 없을 때 |

## 7. 다음 단계 — studyFinal

여기까지가 Reflex의 개별 기능(상태, CRUD, 라우팅, 외부 API, DB, 인증, 배포)을 하나씩 익히는 과정이었습니다. `studyFinal`에서는 이 모든 것을 합쳐 `project/`에 **미니 게시판 웹사이트**를 처음부터 만들어봅니다.
