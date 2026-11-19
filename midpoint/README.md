# midpoint — study0~10의 데모 로그인 게시판

학습 순서·버전·설치·검증 결과는 [루트 README](../README.md)를 따른다.

```powershell
python -m pip install -r requirements.txt
reflex db migrate
reflex run
```

앱 루트에서 실행하고 `http://localhost:3000`에 접속한다. 두 앱을 동시에 실행할 때는 프론트·백엔드 포트와 API URL·허용 origin을 함께 바꾼다. UTF-8 환경변수와 Python 3.12를 사용한다.

로컬 학습용 데모 인증이며 운영 배포용 계정 시스템이 아니다. `/`에서 실습·게시판으로 이동한다.
