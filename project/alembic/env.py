from alembic import context
from project.settings import get_settings
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

from project import models  # noqa: F401

url = get_settings().db_url

config = context.config
config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
target_metadata = SQLModel.metadata

if context.is_offline_mode():
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, render_as_batch=True
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()
