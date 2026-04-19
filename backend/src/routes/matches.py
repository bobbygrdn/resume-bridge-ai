from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel
from src.database import get_db, MatchRecord
from src.schema import MatchRecordOut

router = APIRouter()

@router.get("/matches", response_model=List[MatchRecordOut])
async def get_matches(
    user_id: str = Query(..., description="Filter by user_id (required)"),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(MatchRecord).filter(MatchRecord.user_id == user_id)
    matches = query.order_by(MatchRecord.created_at.desc()).offset(skip).limit(limit).all()
    return matches
