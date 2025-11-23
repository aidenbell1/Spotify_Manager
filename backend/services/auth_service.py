from database import User, Session as SessionModel
from services import database_service
from sqlalchemy import func
from sqlalchemy.orm import Session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES
import secrets
from datetime import datetime, timedelta


sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPES
)

pending_states = {}

def get_current_user(db, session_id: str):
    if not session_id:
        return None
    
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

    if not session or session.expired_at < func.now():
        return None

    user = db.query(User).filter(user.spotify_id == session.user_spotify_id).first()

    if not user:
        return None
    
    return user

def get_spotify_auth_url():
    state = secrets.token_urlsafe(32)
    pending_states[state] = datetime.now()
    auth_url = sp_oauth.get_authorize_url(state=state)
    
    return {"auth_url": auth_url}

def handle_spotify_callback(db: Session, code: str, state: str):
    if not state:
        return {"success": False, "error": "missing_state", "message": "State parameter is missing"}
    
    if state not in pending_states:
        return {"success": False, "error": "invalid_state", "message": "State parameter is invalid or has expired"}
    
    del pending_states[state]

    token_info = sp_oauth.get_access_token(code)
    if not token_info:
        return {"success": False, "error": "token_error", "message": "Failed to retrieve access token from Spotify"}
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user = sp.current_user()
    if not user:
        return {"success": False, "error": "user_error", "message": "Failed to retrieve user info from Spotify"}
    
    new_user = database_service.update_or_create_user(db, user, token_info)

    session_id = secrets.token_urlsafe(32)
    new_session = SessionModel(
        id=session_id,
        user_spotify_id=new_user.spotify_id,
        expires_at=datetime.now() + timedelta(days=7)
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {"success": True, "session_id": session_id, "user": user}
