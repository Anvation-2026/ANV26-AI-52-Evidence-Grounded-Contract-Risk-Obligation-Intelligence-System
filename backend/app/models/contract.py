from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Integer,
    Text,
    TIMESTAMP,
    ForeignKey
)
from sqlalchemy.sql import func

from app.database.connection import Base

# SQLite needs INTEGER affinity for autoincrementing primary keys.
BIGINT_ID = BigInteger().with_variant(Integer, "sqlite")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(
        BIGINT_ID,
        primary_key=True,
        autoincrement=True
    )

    contract_name = Column(
        String(255),
        nullable=False
    )

    # Each uploaded/demo/generated contract belongs to the authenticated account.
    # Nullable only to permit a safe migration of legacy records; legacy unowned
    # records are not visible to authenticated users until explicitly reassigned.
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    file_name = Column(
        String(255),
        nullable=False
    )

    file_type = Column(
        String(50)
    )

    version_number = Column(
        Integer,
        default=1
    )

    parent_contract_id = Column(
        BIGINT_ID,
        ForeignKey(
            "contracts.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    uploaded_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )


class Clause(Base):
    __tablename__ = "clauses"

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

    clause_number = Column(
        String(100)
    )

    clause_title = Column(
        String(255)
    )

    clause_text = Column(
        Text,
        nullable=False
    )

    page_number = Column(
        Integer
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )