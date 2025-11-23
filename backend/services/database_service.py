from database import User, Session as SessionModel
from datetime import datetime

def update_or_create_user(db, user, token_info):
    existing_user = db.query(User).filter(User.spotify_id == user['id']).first()
    
    if existing_user:
        existing_user.access_token = token_info['access_token']
        existing_user.refresh_token = token_info['refresh_token'] 
        existing_user.token_expires_at = datetime.fromtimestamp(token_info['expires_at'])
        db.commit()
    else:
        new_user = User(
            spotify_id=user['id'], 
            display_name=user.get('display_name', ''),
            email=user.get('email', ''),
            country=user.get('country', ''),
            follower_count=user['followers']['total'],
            profile_image_url=user['images'][0]['url'] if user['images'] else '',
            access_token=token_info['access_token'], 
            refresh_token=token_info['refresh_token'],
            token_expires_at=datetime.fromtimestamp(token_info['expires_at'])
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    return existing_user or new_user