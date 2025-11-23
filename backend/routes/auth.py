from fastapi import APIRouter, Depends, Cookie
from sqlalchemy.orm import Session
from database import get_db 
from services import auth_service

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/login")
def login():
    return auth_service.get_spotify_auth_url()

@router.get("/status")
def auth_status(db: Session = Depends(get_db), session_id: str = Cookie(None)):
    user = auth_service.get_current_user(db, session_id)
    if user:
        return {"authenticated": True, "user": user}
    else:
        return {"authenticated": False}

@router.get("/callback")
def callback(code: str=None, state: str=None, error: str=None, db: Session = Depends(get_db)):
    if error:
        return {"success": False, "error": error, "message": "User denied access or error occurred"}
    
    if not code:
        return {"success": False, "error": "missing_code", "message": "No authorization code received"}
        
    return auth_service.handle_spotify_callback(db, code, state)