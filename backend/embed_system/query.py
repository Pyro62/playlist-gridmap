from sqlalchemy import select
from database import SessionLocal
import yt_dlp
import laion_clap
import os
from sqlalchemy.dialects.postgresql import insert
from models import Embedding,Track,DeadLetter
import time
from collections import Counter
import asyncio
import requests

os.makedirs('tmp', exist_ok=True)

model = laion_clap.CLAP_Module(enable_fusion=False, amodel='HTSAT-base')
model.load_ckpt('music_audioset_epoch_15_esc_90.14.pt')

DEAD_LETTER_THRESHOLD = 6
dead_letters_counter = Counter()

async def catalog_dead_letter(deadLetter):
    async with SessionLocal() as db:
        try:
            db.add(deadLetter)
            await db.commit()
        except Exception as e:
            print(f'failed to catalog deadletter')
            await db.rollback()
        
def download_audio(track_name: str, artist_name: str, isrc: str):
    ydl_opts = {
        'format': 'bestaudio/best',          # grab best audio quality
        'outtmpl': f'tmp/{isrc}.%(ext)s',   # where to save it
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',     # extract audio only
            'preferredcodec': 'wav',         # convert to wav
        }],
        'quiet': True,                        # suppress output
        'socket_timeout': 30
    }

    try:
        # 1. download audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{track_name} {artist_name} audio"])
            expected_path = f"tmp/{isrc}.wav"
            if os.path.exists(expected_path):
                return expected_path 
    except Exception as e:
        print(f"Failed Download of {track_name} , {artist_name}, isrc: {isrc} audio")
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
                    await db.execute(insert(Embedding).values(vectors).on_conflict_do_nothing(index_elements=['isrc']))
                    await db.commit()
                except Exception as e:
                    print(f'failed to push embedded tracks')
                    await db.rollback()

BATCH_LIMIT = 20
async def get_unembdedded_tracks():
    tracks = [] # initialize here in case error
    async with SessionLocal() as db:
        
        try:
             result = await db.execute(
                    select(Track)
                    .join(Embedding, Track.isrc == Embedding.isrc, isouter=True)
                    .join(DeadLetter, Track.isrc == DeadLetter.isrc, isouter=True) # Join deadletters
                    .where(Embedding.isrc.is_(None))
                    .where(DeadLetter.isrc.is_(None))                             # Filter them out!
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
        vectors = [] # need to build vector object
        unembeddeds = await get_unembdedded_tracks()
        if unembeddeds:
            print('pulled unembeddeds, processing')
            for track in unembeddeds: # i needa download the track and pass it to embeds
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
                            dead_letter = DeadLetter(isrc=track.isrc,name=track.name,artist=track.artist)
                            print(f"Removing Dead Letter From Queue: {track.isrc} , {track.name} , {track.artist}")
                            await catalog_dead_letter(dead_letter)
                            del dead_letters_counter[track.isrc]

                else:
                    dead_letters_counter[track.isrc] +=1
                    if dead_letters_counter[track.isrc] >= DEAD_LETTER_THRESHOLD:
                        dead_letter = DeadLetter(isrc=track.isrc,name=track.name,artist=track.artist)
                        print(f"Removing Dead Letter From Queue: {track.isrc} , {track.name} , {track.artist}")
                        await catalog_dead_letter(dead_letter)
                        del dead_letters_counter[track.isrc]

            if vectors:
                await catalog_embeds(vectors)
                print(f'Embedded and pushed {len(vectors)} tracks')
                await asyncio.sleep(2)
            sleep_time = 2
        else:
            print('pulled no unembeddeds, sleeping.') 
            await asyncio.sleep(sleep_time)
            sleep_time = min(sleep_time * 2, max_sleep) # if theres no work, sleep longer every check


if __name__ == "__main__":
    asyncio.run(main()) 