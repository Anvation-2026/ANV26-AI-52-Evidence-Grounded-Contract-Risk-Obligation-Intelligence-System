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


class Finding(Base):
    __tablename__ = "findings"

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

    rule_id = Column(
        String(100),
        nullable=False
    )

    category = Column(
        String(100),
        nullable=False
    )

    status = Column(
        String(50),
        nullable=False
    )

    severity = Column(
        String(50),
        nullable=False
    )

    evidence = Column(Text)

    expected = Column(Text)

    actual = Column(Text)

    reason = Column(Text)

    recommended_action = Column(Text)

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )