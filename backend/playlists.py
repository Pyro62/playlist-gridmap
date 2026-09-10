from fastapi import APIRouter, HTTPException, status
from spotify_scraper import AsyncSpotifyClient

import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")    

@router.get("/playlist")
async def get_playlist_tracks(playlist_id: str):
    async with AsyncSpotifyClient() as client:
        try:
            playlist = await client.get_playlist(playlist_id)
            data = playlist.to_dict()
        except Exception as e:
            print(f"Something went wrong with playlist {playlist_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Playlist ingestion failed, Error: {str(e)}"
            )

    return {
        'name': data['name'],
        'description': data['description'],
        'total_tracks': data['total_tracks'],
        'share_url': data['share_url']
    }