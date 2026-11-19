import os

import reflex as rx
from reflex.constants import StateManagerMode

config = rx.Config(
    state_manager_mode=StateManagerMode.MEMORY,
    app_name="midpoint",
    db_url=os.getenv("REFLEX_DB_URL", "sqlite:///midpoint.db"),
    api_url=os.getenv("REFLEX_API_URL", "http://localhost:8000"),
    cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(),
    ],
)
