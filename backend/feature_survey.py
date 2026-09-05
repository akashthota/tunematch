import librosa
import numpy as np
import urllib.request
import httpx
import asyncio
import statistics

GENRE_QUERIES = [
    "pop hits 2026", "rock classics", "hip hop hits", "edm dance",
    "r&b soul", "k-pop", "indie folk", "jazz standards",
    "country hits", "metal", "latin pop", "lofi chill",
]

async def get_tracks():
    tracks = []
    async with httpx.AsyncClient() as client:
        for q in GENRE_QUERIES:
            resp = await client.get("https://api.deezer.com/search", params={"q": q})
            data = resp.json().get("data", [])[:8]
            for t in data:
                tracks.append({
                    "title": t["title"],
                    "artist": t["artist"]["name"],
                    "preview": t["preview"],
                })
    return tracks


def analyze(preview_url):
    path = "temp_survey.mp3"
    urllib.request.urlretrieve(preview_url, path)

    audio, sr = librosa.load(path, sr=None, mono=True)

    tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
    tempo = float(np.atleast_1d(tempo)[0])

    rms = librosa.feature.rms(y=audio)
    energy = float(np.mean(rms))

    centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
    centroid_val = float(np.mean(centroid))

    return tempo, energy, centroid_val


async def main():
    tracks = await get_tracks()
    print(f"Fetched {len(tracks)} candidate tracks. Analyzing...\n")

    results = []
    for i, t in enumerate(tracks):
        try:
            tempo, energy, centroid = analyze(t["preview"])
            results.append({
                "name": f"{t['artist']} - {t['title']}",
                "tempo": tempo, "energy": energy, "centroid": centroid,
            })
            print(f"[{i+1}/{len(tracks)}] OK: {t['artist']} - {t['title']}")
        except Exception as e:
            print(f"[{i+1}/{len(tracks)}] FAILED: {t['artist']} - {t['title']} ({e})")

    print(f"\nSuccessfully analyzed {len(results)} tracks.\n")

    with open("feature_survey_librosa.csv", "w") as f:
        f.write("name,tempo,energy,centroid\n")
        for r in results:
            f.write(f'"{r["name"]}",{r["tempo"]:.2f},{r["energy"]:.6f},{r["centroid"]:.2f}\n')

    for feat in ["tempo", "energy", "centroid"]:
        vals = [r[feat] for r in results]
        print(f"{feat.upper():<12} min={min(vals):.4f}  max={max(vals):.4f}  "
              f"mean={statistics.mean(vals):.4f}  stdev={statistics.stdev(vals):.4f}")

asyncio.run(main())