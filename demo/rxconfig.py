import reflex as rx

config = rx.Config(
    app_name="demo",
    db_url="sqlite:///reflex.db",
    # .env 파일이 있으면 자동으로 읽어서, 아래 값들을 REFLEX_* 환경변수로
    # 덮어쓸 수 있게 해준다 (예: REFLEX_DB_URL, REFLEX_CORS_ALLOWED_ORIGINS).
    # python-dotenv 패키지가 필요하다.
    env_file=".env",
    # 운영 환경에서는 "*" 대신 실제 프론트엔드 배포 도메인만 허용해야 한다.
    cors_allowed_origins=["*"],
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(),
    ],
)
