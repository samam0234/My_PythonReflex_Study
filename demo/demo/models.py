import sqlmodel


class FruitRecord(sqlmodel.SQLModel, table=True):
    """데이터베이스 테이블 하나에 대응하는 모델.

    옛 Reflex 튜토리얼에서 보이는 `rx.Model`은 0.9.2부터 지원 종료(deprecated)
    되었고, 공식적으로 "SQLAlchemy/SQLModel을 직접 쓰라"고 안내한다. 그래서
    여기서는 `sqlmodel.SQLModel`을 바로 상속한다. Reflex는 `rx.session()`으로
    `rxconfig.py`의 `db_url`에 연결된 세션을 내어줄 뿐, 모델 정의 자체는
    순수 SQLModel/SQLAlchemy 영역이다.
    """

    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    name: str
    in_stock: bool = True
