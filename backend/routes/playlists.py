from fastapi import APIRouter, HTTPException, status
from spotify_scraper import AsyncSpotifyClient
from models import Track as TrackModel
from database import SessionLocal
from sqlalchemy.dialects.postgresql import insert
import logging

logger = logging.getLogger(__name__)

import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")   


def validate_playlist_url(playlist_url: str): # todo make validator and pass it in
    return


@router.post("/playlist/ingest")
async def get_playlist_tracks(playlist_id: str):
    async with AsyncSpotifyClient() as client:
        try:    
            playlist = await client.get_playlist(playlist_id, max_tracks=None)
            data = playlist.to_dict()
        except Exception as e:
            logger.exception(f"Something went wrong with playlist {playlist_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Playlist ingestion failed, Error: {str(e)}"
            )
    trackVector = []
    for playlist_track in data.get('tracks') or []: # if data.get() yields none then iterate through empty
        track = playlist_track.get('track')
        if not track:
            continue
        
        artist_names = ", ".join(a['name'] for a in track.get('artists', []))
        album_name = track['album']['name'] if track.get('album') else None
        image_url = track['images'][0]['url'] if track.get('images') else None

        trackVector.append(
            {
                "isrc": track['uri'],  # should be isrc but whatever
                "name": track.get('name'),
                "artist": artist_names,
                "album": album_name,
                "duration_ms": track.get('duration_ms'),
                "image_url": image_url,

        })
    
    if trackVector:
        async with SessionLocal() as db:
            try:
                await db.execute(insert(TrackModel).values(trackVector).on_conflict_do_nothing(index_elements=['isrc']))
                await db.commit()
            except Exception:
                logger.exception(f"Failed to push tracks for playlist {playlist_id}")
                await db.rollback()
    return {
        'name': data['name'],
        'description': data['description'],
        'total_tracks': data['total_tracks'],
        'share_url': data['share_url']
    }