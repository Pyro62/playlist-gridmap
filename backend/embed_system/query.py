from sqlalchemy import select
from database import SessionLocal
import yt_dlp
import laion_clap
import os
from sqlalchemy.dialects.postgresql import insert
from models import FullEmbedding,Track,DeadLetterFull, PreviewEmbedding,DeadLetterPreview
from collections import Counter
import asyncio
import time
from spotify_scraper import AsyncSpotifyClient
class QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(msg)


os.makedirs('tmp', exist_ok=True)

model = laion_clap.CLAP_Module(enable_fusion=False, amodel='HTSAT-base')
model.load_ckpt('music_audioset_epoch_15_esc_90.14.pt')

DEAD_LETTER_THRESHOLD = 6
dead_letters_counter = Counter()

DEAD_LETTER_PREVIEW_THRESHOLD = 1
dead_letters_preview_counter = Counter()

async def catalog_dead_letter(deadLetter):
    async with SessionLocal() as db:
        try:
            db.add(deadLetter)
            await db.commit()
        except Exception as e:
            print(f'failed to catalog deadletter error: {e}')
            await db.rollback()

async def download_preview(uri: str):
        try:
            async with AsyncSpotifyClient() as client:
                track = await client.get_track(uri)
                filename = uri[14:]
                preview_path = await client.download_preview(entity=track, dest='tmp',filename=f"{filename}.mp3")
                print(f"downloading preview for {track.name}")
                if os.path.exists(preview_path):
                    return preview_path
        except Exception as e:
            print(f"Failed preview download for {uri}, error: {e}")
            return None
           
def download_audio(track_name: str, artist_name: str, isrc: str):
    safe_id = isrc.replace(":", "_")  # filesystem-safe version, just for the path
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'tmp/{safe_id}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'quiet': True,
        'socket_timeout': 30,
        # Fix 403 Forbidden errors
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
        'source_address': '0.0.0.0', # Force IPv4
        'logger': QuietLogger()
    }

    try:
        # 1. download audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{track_name} {artist_name} audio"])
            expected_path = f"tmp/{safe_id}.wav"
            if os.path.exists(expected_path):
                time.sleep(0.5)
                return expected_path 
    except Exception as e:
        print(f"Failed Download of {track_name} , {artist_name}, isrc: {isrc} audio {e}")
        return None

def embed_track(filepath):
    try:
        embedding = model.get_audio_embedding_from_filelist([filepath], use_tensor=False)
        vector = embedding[0].tolist()
        return vector
    except Exception as e:
        print(f"Error generating embedding for {filepath}: {e}")
        return None
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


# Embedding has isrc, embedding, todo is build the Embedding object first., then a big arr of embedding objects before pushing
async def catalog_embeds(vectors):
    async with SessionLocal() as db:
                try:
                    await db.execute(insert(FullEmbedding).values(vectors).on_conflict_do_nothing(index_elements=['isrc']))
                    await db.commit()
                except Exception as e:
                    print(f'failed to push embedded tracks {e}')
                    await db.rollback()
async def catalog_preview_embeds(vectors):
    async with SessionLocal() as db:
        try:
            await db.execute(insert(PreviewEmbedding).values(vectors).on_conflict_do_nothing(index_elements=['isrc']))
            await db.commit()
        except Exception as e:
            print(f'Failed to push embedded previews {e}')
            await db.rollback()

BATCH_LIMIT = 20
async def get_unembedded_previews():
    tracks = []
    async with SessionLocal() as db:
            try:
                 result = await db.execute(
                        select(Track)
                        .join(PreviewEmbedding, Track.isrc == PreviewEmbedding.isrc, isouter=True)
                        .join(DeadLetterPreview, Track.isrc == DeadLetterPreview.isrc, isouter=True) # Join deadletters
                        .where(PreviewEmbedding.isrc.is_(None))
                        .where(DeadLetterPreview.isrc.is_(None))                             # Filter them out!
                        .limit(BATCH_LIMIT)
                    )
                 tracks = result.scalars().all()
                 print(f'pulled {len(tracks)} unembedded previews')
            except Exception as e:
                 print(f"Error handling unembedded preview retrieval: {str(e)}")
                 await db.rollback()
    return tracks

async def get_unembedded_tracks():
    tracks = [] # initialize here in case error
    async with SessionLocal() as db:
        
        try:
             result = await db.execute(
                    select(Track)
                    .join(FullEmbedding, Track.isrc == FullEmbedding.isrc, isouter=True)
                    .join(DeadLetterFull, Track.isrc == DeadLetterFull.isrc, isouter=True) # Join deadletters
                    .where(FullEmbedding.isrc.is_(None))
                    .where(DeadLetterFull.isrc.is_(None))                             # Filter them out!
                    .limit(BATCH_LIMIT)
                )
             tracks = result.scalars().all()
             print(f'pulled {len(tracks)} unembedded tracks')
        except Exception as e:
             print(f"Error handling unembedded track retrieval: {str(e)}")
             await db.rollback()
    return tracks

max_sleep = 10
sleep_time = 2
async def main():
    global sleep_time
    global max_sleep
    while True:
        vectors = [] # arr of vectors to be pushed to db
        previewVectors = []
        fullUnembeddeds = await get_unembedded_tracks()
        previewUnembeddeds = await get_unembedded_previews()

        if previewUnembeddeds:
            print('pulled previews, processing')
            for preview in previewUnembeddeds:
                filepath = await download_preview(preview.isrc)

                if filepath:
                    vector = await asyncio.to_thread(embed_track,filepath)
                    if vector is not None:
                        previewVectors.append(
                            {
                                'isrc': preview.isrc,
                                'embedding': vector
                            }
                        )
                    else: # means embed_track returns none, ie no file, handle deadletter.
                        dead_letters_preview_counter[preview.isrc] +=1
                        if dead_letters_preview_counter[preview.isrc] >= DEAD_LETTER_PREVIEW_THRESHOLD:
                            dead_letter = DeadLetterPreview(isrc=preview.isrc,name=preview.name,artist=preview.artist)
                            print(f"Removing Dead Letter From Queue: {preview.isrc} , {preview.name} , {preview.artist}")
                            await catalog_dead_letter(dead_letter)
                            del dead_letters_preview_counter[preview.isrc]
                else:
                    dead_letters_preview_counter[preview.isrc] +=1
                    if dead_letters_preview_counter[preview.isrc] >= DEAD_LETTER_PREVIEW_THRESHOLD:
                        dead_letter = DeadLetterPreview(isrc=preview.isrc,name=preview.name,artist=preview.artist)
                        print(f"Removing Dead Letter From Queue: {preview.isrc} , {preview.name} , {preview.artist}")
                        await catalog_dead_letter(dead_letter)
                        del dead_letters_preview_counter[preview.isrc]



            if previewVectors:
                await catalog_preview_embeds(previewVectors)
                print(f'Embedded and pushed{len(previewVectors)} previews')
        else:
            print('pulled no previews, moving onto fulls')
            
        if fullUnembeddeds:
            print('pulled unembeddeds, processing')
            for track in fullUnembeddeds: # i needa download the track and pass it to embeds
                print(f'downloading {track.name} ')
                filepath = await asyncio.to_thread(download_audio, track.name, track.artist, track.isrc)
                
                if filepath:
                    vector = await asyncio.to_thread(embed_track, filepath)
                    if vector is not None:
                        vectors.append({
                        'isrc': track.isrc,
                        'embedding': vector
                        
                        })
                        dead_letters_counter.pop(track.isrc, None)
                    else:
                        dead_letters_counter[track.isrc] +=1
                        if dead_letters_counter[track.isrc] >= DEAD_LETTER_THRESHOLD:
                            dead_letter = DeadLetterFull(isrc=track.isrc,name=track.name,artist=track.artist)
                            print(f"Removing Dead Letter From Queue: {track.isrc} , {track.name} , {track.artist}")
                            await catalog_dead_letter(dead_letter)
                            del dead_letters_counter[track.isrc]

                else:
                    dead_letters_counter[track.isrc] +=1
                    if dead_letters_counter[track.isrc] >= DEAD_LETTER_THRESHOLD:
                        dead_letter = DeadLetterFull(isrc=track.isrc,name=track.name,artist=track.artist)
                        print(f"Removing Dead Letter From Queue: {track.isrc} , {track.name} , {track.artist}")
                        await catalog_dead_letter(dead_letter)
                        del dead_letters_counter[track.isrc]

            if vectors:
                await catalog_embeds(vectors)
                print(f'Embedded and pushed {len(vectors)} tracks')
                await asyncio.sleep(2)
            sleep_time = 2
        else:
            if previewUnembeddeds:
                print('no full embeds, skipping sleep to work previews')
                continue
            else:
                print('pulled no unembeddeds, sleeping.') 
                await asyncio.sleep(sleep_time)
                sleep_time = min(sleep_time * 2, max_sleep) # if theres no work, sleep longer every check


if __name__ == "__main__":
    asyncio.run(main()) 