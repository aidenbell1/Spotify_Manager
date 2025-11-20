from fastapi import FastAPI
from database import createTables, dropTables

app = FastAPI()

# Create database tables on startup
createTables()

@app.get("/")
def read_root():
    return {"message": "Spotify Dashboard API"}