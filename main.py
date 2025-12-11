# File: main.py
import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from io import BytesIO
from PIL import Image

import service
import crud
import database
from schemas import InvoiceData

app = FastAPI(title="Invoice Extraction API (Postgres Single Table)", root_path="/invoice")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.title = "Invoice Extractor V2 (Single Table)"

# Initialize DB tables on startup
@app.on_event("startup")
async def startup_event():
    await database.init_db()

# Custom endpoint to serve the HTML file at the root URL (/)
@app.get("/", include_in_schema=False)
async def serve_admin_panel():
    """Serves the index.html file."""
    try:
        with open("index.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: index.html not found.</h1><p>Please ensure index.html is in the same directory as main.py.</p>", status_code=404)


# --- API Endpoints ---

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Invoice Extractor V2 (Single Table)"}

@app.post("/api/upload", response_model=Dict[str, Any])
async def upload_invoice(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Upload an invoice (PDF or Image).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    content_type = file.content_type
    
    pil_image = None

    try:
        if "application/pdf" in content_type:
            images = service.pdf_to_images(content)
            if not images:
                raise HTTPException(status_code=400, detail="Empty PDF file")
            pil_image = images[0]
        elif "image" in content_type:
            pil_image = Image.open(BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF or Image.")

        validated_data: InvoiceData = await service.process_invoice_with_vllm(pil_image)

        log_record = await crud.create_invoice_log(
            db=db, 
            filename=file.filename, 
            file_bytes=content, 
            data=validated_data
        )

        return {
            "message": "Success",
            "log_id": log_record.id,
            "data": validated_data
        }

    except Exception as e:
        print(f"Error during upload/processing: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/api/logs")
async def read_logs(
    skip: int = 0, 
    limit: int = 10, 
    search: Optional[str] = Query(None, description="Search term"),
    type: Optional[str] = Query("filename", description="Search by 'filename' or 'id'"),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Read logs from PostgreSQL with pagination and search.
    """
    logs = await crud.get_invoice_logs_metadata(
        db, 
        skip=skip, 
        limit=limit, 
        search_query=search, 
        search_type=type
    )
    
    return [
        {
            "id": row.id,
            "filename": row.filename,
            "created_at": row.created_at,
            "extracted_schema_content": row.extracted_schema_content,
            "file_size": row.file_size
        } 
        for row in logs
    ]

@app.get("/api/logs/{log_id}/preview")
async def preview_log_image(log_id: int, db: AsyncSession = Depends(database.get_db)):
    """
    Fetches the raw bytes from DB, converts to an image in memory, 
    and streams it back.
    """
    log = await crud.get_invoice_log_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    try:
        file_bytes = log.file_content
        output_image = None
        
        try:
            output_image = Image.open(BytesIO(file_bytes))
        except IOError:
            try:
                images = service.pdf_to_images(file_bytes)
                if images:
                    output_image = images[0]
            except Exception:
                pass
        
        if output_image is None:
             raise HTTPException(status_code=400, detail="Could not convert file content to image preview.")

        img_buffer = BytesIO()
        output_image = output_image.convert("RGB")
        output_image.save(img_buffer, format="JPEG")
        img_buffer.seek(0)
        
        return StreamingResponse(img_buffer, media_type="image/jpeg")

    except Exception as e:
        print(f"Error during preview generation: {e}")
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")

# --- STATIC FILE SERVER (Fix for 404 images) ---
@app.get("/{filename}")
async def serve_static_file(filename: str):
    """
    Serves static files (images, logos, favicon) from the root directory.
    Only serves safe extensions to prevent source code leaking.
    """
    # 1. Security Check: Allow only specific extensions
    allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".css", ".js"}
    _, ext = os.path.splitext(filename)
    
    if ext.lower() not in allowed_extensions:
        raise HTTPException(status_code=404, detail="File type not allowed")

    # 2. Path Traversal Check
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=404, detail="Invalid filename")

    # 3. Serve File
    file_path = os.path.join(".", filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    print("--- Invoice Extractor V2 (Backend & Frontend) Starting ---")
    uvicorn.run("main:app", host="0.0.0.0", port=8501, reload=True)