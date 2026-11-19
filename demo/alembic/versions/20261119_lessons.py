import sqlalchemy as sa
from alembic import op

revision = "20261119_lessons"
down_revision = "1677fb0458f0"
branch_labels = None
depends_on = None


def upgrade():
    for name in ("lessonpost", "authpost"):
        op.create_table(
            name,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("author", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )


def downgrade():
    op.drop_table("authpost")
    op.drop_table("lessonpost")
