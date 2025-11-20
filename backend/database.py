from config import DATABASE_URL

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, func, Text, Float
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

database = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database)

class User(Base):
    __tablename__ = "users"
    spotify_id = Column(String, primary_key=True, index=True)
    display_name = Column(String)
    follower_count = Column(Integer)
    profile_image_url = Column(String)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

class Track(Base):
    __tablename__ = "track"
    spotify_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    duration_ms = Column(Integer)
    popularity = Column(Integer)
    album_name = Column(String)
    release_date = Column(String)

class Artist(Base):
    __tablename__ = "artist"
    spotify_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    genre = Column(Text)
    popularity = Column(Integer)
    follower_count = Column(Integer)

class AudioFeatures(Base):
    __tablename__ = "audio_features"
    track_spotify_id = Column(String, ForeignKey("track.spotify_id"), primary_key=True)
    danceability = Column(Float)
    energy = Column(Float)
    key = Column(Float)
    loudness = Column(Float)
    mode = Column(Float)
    speechiness = Column(Float)
    acousticness = Column(Float)
    instrumentalness = Column(Float)
    liveness = Column(Float)
    valence = Column(Float)
    tempo = Column(Float)
    time_signature = Column(Float)

class UserTopTracks(Base):
    __tablename__ = "user_top_tracks"
    id = Column(Integer, primary_key=True, index=True)
    user_spotify_id = Column(String, ForeignKey("users.spotify_id"))
    track_spotify_id = Column(String, ForeignKey("track.spotify_id"))
    rank = Column(Integer)
    time_range = Column(String)
    added_at = Column(DateTime, default=func.now())

class UserRecentTracks(Base):
    __tablename__ = "user_recent_tracks"
    id = Column(Integer, primary_key=True, index=True)
    user_spotify_id = Column(String, ForeignKey("users.spotify_id"))
    track_spotify_id = Column(String, ForeignKey("track.spotify_id"))
    played_at = Column(DateTime)

def createTables():
    Base.metadata.create_all(bind=database)

def dropTables():
    Base.metadata.drop_all(bind=database)