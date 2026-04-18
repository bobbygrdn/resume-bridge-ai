from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pathlib import Path
import shutil
import os
from llama_index.readers.file import PyMuPDFReader
from src.engine import process_resume_pdf, default_storage_context

router = APIRouter()

reader = PyMuPDFReader()

@router.post("/upload_resume")
async def upload_resume(user_id: str, file: UploadFile = File(...)):
    temp_path = f"data/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        documents = reader.load_data(file_path=Path(temp_path))
        raw_text = "\n".join([doc.text for doc in documents])
        profile = await process_resume_pdf(raw_text, default_storage_context, user_id)
        return {"message": "Identity indexed", "profile": profile}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)
