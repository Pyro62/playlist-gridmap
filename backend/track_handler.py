import requests
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal
from models import Track
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

#todo handle error in case func fails.
# also add liked songs to list
# and remove column preview url, its depreciated
async def catalog_user_tracks(access_token: str):
    async with SessionLocal() as db:
        response = requests.get(
            "https://api.spotify.com/v1/me/playlists",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 50}
        )
        playlists = response.json()

        if 'items' not in playlists:
            print(f"Failed to get playlists: {playlists}")
            return

        for playlist in playlists['items']:
            response = requests.get(
            f"https://api.spotify.com/v1/playlists/{playlist['id']}/items",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 100}
            )
            data = response.json()  # call once, store it
            
            if 'items' not in data:
                print(f"Skipping playlist, unexpected response: {data}")
                continue
            tracks = catalog_tracks(data)
            

            while data.get('next'):
                response = requests.get(data["next"], headers={"Authorization": f"Bearer {access_token}"})
                data = response.json()
                tracks.extend(catalog_tracks(data))
            
            if tracks:
                await db.execute(insert(Track).values(tracks).on_conflict_do_nothing(index_elements=["isrc"]))
                await db.commit()
    return

def catalog_tracks(data):
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
            "preview_url": track.get("preview_url"),
            "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None
        })
    return arr