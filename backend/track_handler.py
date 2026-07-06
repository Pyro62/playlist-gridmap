import requests
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal
from models import Track
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

#todo handle error in case func fails.
async def catalog_user_tracks(access_token: str):
    async with SessionLocal() as db:
        response = requests.get(
            "https://api.spotify.com/v1/me/playlists",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 50}
        )
        playlists = response.json()

        for playlist in playlists['items']:
            response = requests.get(
            f"https://api.spotify.com/v1/playlists/{playlist['id']}/tracks",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 100}
            )

            data = response.json()
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
            if item['track']==None:
                continue

            track = item["track"]
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
     