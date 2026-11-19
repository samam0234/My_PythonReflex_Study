import sqlalchemy as sa
from alembic import op

revision = "20261119_midpoint"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "midpoint_post",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("midpoint_post")
