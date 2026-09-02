import os
import httpx
import essentia.standard as es
from database import get_cached_analysis, save_analysis


async def analyze_track(track_id, source, preview_url):
    cached = get_cached_analysis(track_id)
    if cached:
        return cached

    if not preview_url:
        return None

    temp_path = f"/tmp/preview_{track_id}.mp3"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(preview_url, timeout=10.0)
            if response.status_code != 200 or len(response.content) < 1000:
                print(f"Preview download failed for {track_id}: status={response.status_code}, size={len(response.content)}")
                return None
            with open(temp_path, "wb") as f:
                f.write(response.content)

        loader = es.MonoLoader(filename=temp_path)
        audio = loader()

        rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
        bpm, _, beats_confidence, _, _ = rhythm_extractor(audio)

        raw_energy = es.Energy()(audio)
        normalized_energy = raw_energy / len(audio)  # average energy per sample, not affected by clip length/gain

        save_analysis(track_id, source, float(bpm), float(normalized_energy))
        return {"tempo": float(bpm), "energy": float(normalized_energy)}

    except Exception as e:
        print(f"Analysis failed for track {track_id}: {e}")
        return None

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)