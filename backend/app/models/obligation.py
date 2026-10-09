from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    TIMESTAMP,
    ForeignKey
)
from sqlalchemy.sql import func

from app.database.connection import Base

# SQLite needs INTEGER affinity for autoincrementing primary keys.
BIGINT_ID = BigInteger().with_variant(Integer, "sqlite")


class Obligation(Base):
    __tablename__ = "obligations"

    id = Column(
        BIGINT_ID,
        primary_key=True,
        autoincrement=True
    )

    contract_id = Column(
        BIGINT_ID,
        ForeignKey(
            "contracts.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    clause_id = Column(
        BIGINT_ID,
        ForeignKey(
            "clauses.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    actor = Column(
        String(255)
    )

    action = Column(
        Text
    )

    deadline = Column(
        String(255)
    )

    trigger_condition = Column(
        Text
    )

    evidence = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )