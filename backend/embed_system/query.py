from sqlalchemy import select
from database import SessionLocal
import yt_dlp
import laion_clap
import os
from sqlalchemy.dialects.postgresql import insert
from models import Embedding,Track
import time

model = laion_clap.CLAP_Module(enable_fusion=False, amodel='HSAT-submel')
model.load_ckpt('music_audioset_epoch_15_esc_90.14.pt')


def download_audio(track_name: str, artist_name: str, isrc: str):
    ydl_opts = {
        'format': 'bestaudio/best',          # grab best audio quality
        'outtmpl': f'tmp/{isrc}.%(ext)s',   # where to save it
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',     # extract audio only
            'preferredcodec': 'wav',         # convert to wav
        }],
        'quiet': True                        # suppress output
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
def catalog_embeds(vectors):
    with SessionLocal() as db:
                try:
                    db.execute(insert(Embedding).values(vectors).on_conflict_do_nothing(index_elements=['isrc']))
                    db.commit()
                except Exception as e:
                    print(f'failed to push embedded tracks')
                    db.rollback()

BATCH_LIMIT = 20
def get_unembdedded_tracks():
    tracks = [] # initialize here in case error
    with SessionLocal() as db:
        try:
             result = db.execute(select(Track)
                            .join(Embedding, Track.isrc == Embedding.isrc, isouter=True)
                            .where(Embedding.isrc.is_(None))
                            .limit(BATCH_LIMIT)
                            )
             tracks = result.scalars().all()
        except Exception as e:
             print(f"Error handling unembedded track retrieval: {str(e)}")
             db.rollback()
    return tracks

max_sleep = 10
sleep_time = 2
while True:
    vectors = [] # need to build vector object
    unembeddeds = get_unembdedded_tracks()
    if unembeddeds:
        for track in unembeddeds: # i needa download the track and pass it to embeds
            filepath = download_audio(track.name,track.artist,track.isrc)
            if filepath:
                vector = embed_track(filepath)
                if vector is not None:
                    vectors.append({
                    'isrc': track.isrc,
                    'embedding': vector
                    
                    })
        if vectors:
            catalog_embeds(vectors)
        sleep_time = 2
    else: 
        time.sleep(sleep_time)
        sleep_time = min(sleep_time * 2, max_sleep) # if theres no work, sleep longer every check

    