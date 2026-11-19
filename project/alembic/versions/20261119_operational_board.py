"""study16: 계정·만료 세션·요청 한도·소유권과 정렬 인덱스.

기존 글은 owner_id=NULL로 유지한다. 사용자에게 임의 귀속시키지 않는다.
"""

import sqlalchemy as sa
from alembic import op

revision = "20261119_board"
down_revision = "c730dbc292db"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_user_username", "user", ["username"], unique=True)
    with op.batch_alter_table("post") as batch:
        batch.add_column(sa.Column("owner_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
        batch.create_foreign_key("fk_post_owner_id_user", "user", ["owner_id"], ["id"])
        batch.create_index("ix_post_owner_id", ["owner_id"])
        batch.create_index("ix_post_created_id", ["created_at", "id"])
    op.create_table(
        "loginsession",
        sa.Column("token_hash", sa.String(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
    )
    op.create_index("ix_loginsession_user_id", "loginsession", ["user_id"])
    op.create_index("ix_loginsession_expires_at", "loginsession", ["expires_at"])
    op.create_table(
        "ratewindow",
        sa.Column("subject", sa.String(), primary_key=True),
        sa.Column("window", sa.Integer(), primary_key=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
    )
    op.create_table(
        "aidaily",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), primary_key=True),
        sa.Column("day", sa.String(), primary_key=True),
        sa.Column("calls", sa.Integer(), nullable=False),
    )


def downgrade():
    op.drop_table("aidaily")
    op.drop_table("ratewindow")
    op.drop_table("loginsession")
    with op.batch_alter_table("post") as batch:
        batch.drop_index("ix_post_created_id")
        batch.drop_index("ix_post_owner_id")
        batch.drop_constraint("fk_post_owner_id_user", type_="foreignkey")
        batch.drop_column("revision")
        batch.drop_column("owner_id")
    op.drop_table("user")
