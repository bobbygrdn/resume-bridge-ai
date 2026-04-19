from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from src.database import get_db, MatchRecord

router = APIRouter()

@router.post("/archive-match/{match_id}")
async def archive_match(match_id: int, db: Session = Depends(get_db)):
    record = db.query(MatchRecord).filter(MatchRecord.id == match_id).first()
    if record:
        record.archived = True
        db.commit()
        return {"message": "Match archived successfully."}
    return JSONResponse(status_code=404, content={"detail": "Match not found."})
