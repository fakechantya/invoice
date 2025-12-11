# File: models.py
from sqlalchemy import Column, Integer, String, DateTime, LargeBinary
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base

# 1. The "Log" Table (Stores Log Info, File, Schema Content)
# This now serves as the single source of truth for both the file and the data.
class InvoiceLog(Base):
    __tablename__ = "invoice_logs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_content = Column(LargeBinary, nullable=False) # Stores the raw PDF/Image bytes
    extracted_schema_content = Column(JSONB, nullable=False) # Stores the extracted JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())