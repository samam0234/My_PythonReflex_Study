import reflex as rx

config = rx.Config(
    app_name="project",
    db_url="sqlite:///reflex.db",
    env_file=".env",
    cors_allowed_origins=["*"],
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(),
    ],
)
