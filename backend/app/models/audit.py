from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.database.connection import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(80), nullable=False)
    description = Column(Text, nullable=False)
    details_json = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)

class ReviewAction(Base):
    __tablename__ = "review_actions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(40), nullable=False, default="OPEN")
    note = Column(Text, default="")
    reviewer = Column(String(120), default="Reviewer")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
