# File: crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from models import InvoiceLog
from schemas import InvoiceData
from typing import List, Optional

# --- Log Operations ---

async def create_invoice_log(
    db: AsyncSession, 
    filename: str, 
    file_bytes: bytes, 
    data: InvoiceData
) -> InvoiceLog:
    """
    Stores the log, file blob, and schema content in the Postgres Log table.
    """
    db_log = InvoiceLog(
        filename=filename,
        file_content=file_bytes,
        extracted_schema_content=data.model_dump(mode='json')
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log

async def get_invoice_logs_metadata(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 10, 
    search_query: str = None, 
    search_type: str = "filename"
):
    """
    Fetches log metadata and file size with optional filtering and pagination.
    """
    stmt = (
        select(
            InvoiceLog.id,
            InvoiceLog.filename,
            InvoiceLog.created_at,
            InvoiceLog.extracted_schema_content,
            func.length(InvoiceLog.file_content).label("file_size")
        )
        .order_by(InvoiceLog.created_at.desc())
    )

    # Apply Search Filter
    if search_query:
        if search_type == "id":
            # Only filter by ID if query is a valid integer
            if search_query.isdigit():
                stmt = stmt.where(InvoiceLog.id == int(search_query))
            else:
                # If searching by ID but text is not int, return nothing
                stmt = stmt.where(InvoiceLog.id == -1) 
        else:
            # Default to filename search (case-insensitive)
            stmt = stmt.where(InvoiceLog.filename.ilike(f"%{search_query}%"))

    # Apply Pagination
    stmt = stmt.offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    return result.all()

async def get_invoice_log_by_id(db: AsyncSession, log_id: int) -> Optional[InvoiceLog]:
    """
    Fetches a single invoice log by ID.
    """
    stmt = select(InvoiceLog).where(InvoiceLog.id == log_id)
    result = await db.execute(stmt)
    return result.scalars().first()