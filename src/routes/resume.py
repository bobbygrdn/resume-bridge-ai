from fastapi import APIRouter, UploadFile, File
import os
from src.services import process_resume_upload

router = APIRouter()

@router.post("/upload_resume")
async def upload_resume(user_id: str, file: UploadFile = File(...)):
    temp_path = f"tempData/{file.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
    try:
        result = await process_resume_upload(temp_path, user_id)
        return result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
