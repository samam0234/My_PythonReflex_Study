import reflex as rx
from project.settings import get_settings
from reflex.constants import StateManagerMode

settings = get_settings()
config = rx.Config(
    state_manager_mode=StateManagerMode.MEMORY,
    app_name="project",
    db_url=settings.db_url,
    api_url=settings.api_url,
    cors_allowed_origins=list(settings.origins),
    env_file=".env",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(appearance="light", accent_color="indigo", radius="medium")
        ),
    ],
)
