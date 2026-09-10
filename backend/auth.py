from datetime import datetime, timedelta, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import requests
import jwt
import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends
import random, string
from fastapi.responses import RedirectResponse
from track_handler import catalog_user_tracks
from database import get_db, engine
from models import User
router = APIRouter()
import asyncio
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")    
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

@router.get("/auth/callback")
async def callback(code: str, db: AsyncSession = Depends(get_db)): # endpoint that user hits after /authorize
    # todo, verify state from frontend to backend
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code", # calls spotify api with code from /callback after auth
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(url,data=data)
    tokens = response.json() # stuff accessed via tokens[yada yada]
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    expires_in = tokens["expires_in"]
    
    me_url = "https://api.spotify.com/v1/me"
    me_response =requests.get(me_url, 
                 headers={"Authorization": f"Bearer {access_token}"})
    profile = me_response.json()

    spotify_id = profile['id']
    display_name = profile.get('display_name')
    email = profile.get('email')

    result = await db.execute(select(User).where(User.spotify_id == spotify_id))
    user = result.scalar_one_or_none() #returns the user object if found, None otherwise, returns one thingy

    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

    if user:
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.token_expires_at = expires_at
    else:
        user = User(
            spotify_id = spotify_id,
            display_name = display_name,
            email = email,
            access_token=access_token,
            refresh_token = refresh_token,
            token_expires_at = expires_at
        )
        db.add(user)
    await db.commit() # commits, executes
    await db.refresh(user) # refreshes so it generates id from primary key and stuff

    asyncio.create_task(catalog_user_tracks(access_token))

    jwt_token = jwt.encode({'user_id' : user.id}, os.getenv("JWT_SECRET"), algorithm="HS256")
    return {'token':jwt_token}

def generateRandomString(length: int):
    characters = string.ascii_letters + string.digits
    
    # Select 'length' number of random characters and join them
    return ''.join(random.choices(characters, k=length))

@router.get('/auth/login')
async def login():
    state = generateRandomString(16)
    scope = 'user-read-email user-top-read playlist-read-private playlist-read-collaborative user-library-read'
    
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'state': state,
        'scope': scope
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    url = f"https://accounts.spotify.com/authorize?{query_string}"
    
    return RedirectResponse(url)
# return code to frontend for callback