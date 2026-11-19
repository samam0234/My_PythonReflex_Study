# project — study11~18을 연결한 최종 게시판

학습 순서·버전·설치·검증 결과는 [루트 README](../README.md)를 따른다.

```powershell
python -m pip install -r requirements.txt
reflex db migrate
reflex run
```

앱 루트에서 실행하고 `http://localhost:3000`에 접속한다. 두 앱을 동시에 실행할 때는 프론트·백엔드 포트와 API URL·허용 origin을 함께 바꾼다. UTF-8 환경변수와 Python 3.12를 사용한다.

최종 앱은 DB 계정을 사용한다. 로컬에서 `python -m project.manage seed-demo` 후 `demo / demo-password-123`, `guest / guest-password-123`으로 시험할 수 있다. 운영에서는 `create-user`로 계정을 만들고 APP_ENV=production을 사용한다.

AI는 서버의 OPENAI_API_KEY·AI_MODEL 설정 후 사용한다. MCP read-only 도구는 설정 없이 `/dashboard`에서 실행할 수 있다. 기존 글 소유권은 자동 귀속하지 않는다.

[최종 과정](../studyFinal.md), [배포](../deploy/README.md)
