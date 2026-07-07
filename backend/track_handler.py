import requests
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import httpx
from database import SessionLocal
from models import Track
from sqlalchemy.dialects.postgresql import insert

#todo handle error in case func fails.
# and remove column preview url, its depreciated
# do httpx so no blopcking the jwt loop
async def catalog_user_tracks(access_token: str):
    async with SessionLocal() as db:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                "https://api.spotify.com/v1/me/playlists",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"limit": 50}
                )
                playlists = response.json()

                if 'items' not in playlists:
                    print(f"Failed to get playlists: {playlists}")
                    return

                tracks =[]
                saved_tracks = await get_saved_tracks(access_token, client)
                tracks.extend(saved_tracks)
                for playlist in playlists['items']:
                    response = await client.get(
                    f"https://api.spotify.com/v1/playlists/{playlist['id']}/items",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={"limit": 100}
                    )
                    data = response.json()  # call once, store it
                    
                    if 'items' not in data:
                        print(f"Skipping playlist {playlist['name']}, unexpected response: {data}")
                        continue
                    tracks.extend(get_tracks(data))
                    

                    while data.get('next'):
                        response = await client.get(data["next"], headers={"Authorization": f"Bearer {access_token}"})
                        data = response.json()
                        tracks.extend(get_tracks(data))
                    
                if tracks:
                        await db.execute(insert(Track).values(tracks).on_conflict_do_nothing(index_elements=["isrc"]))
                        await db.commit()
            except Exception as e:
                print(f"Error handling track cataloging: {str(e)}")
                await db.rollback()

    return

def get_tracks(data):
    arr = []
    for item in data["items"]:
        if item is None:
            continue
        
        track = item.get("track") or item.get("item")
        
        if track is None:
            continue
            
        if track.get("type") != "track":  # skip episodes/podcasts
            continue

        isrc = track["external_ids"].get("isrc")
        if not isrc:
            continue
            
        arr.append({
            "isrc": isrc,
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "duration_ms": track["duration_ms"],
            "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None
        })
    return arr

async def get_saved_tracks(access_token, client: httpx.AsyncClient):
    arr=[]
    response = await client.get(
        "https://api.spotify.com/v1/me/tracks",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 50}
        )
    tracks = response.json()
    arr.extend(get_tracks(tracks))

    while tracks.get('next'):
        response = client.get(tracks["next"], headers={"Authorization": f"Bearer {access_token}"})
        tracks = response.json()
        arr.extend(get_tracks(tracks))
    return arr