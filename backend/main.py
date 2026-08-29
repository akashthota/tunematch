import httpx
from fastapi import FastAPI

app = FastAPI(title="TuneMatch API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/resolve")
async def resolve_track(q: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.deezer.com/search",
            params={"q": q},
        )
        data = response.json()

        candidates = []
        for track in data.get("data", [])[:10]:
            candidates.append({
                "id": track["id"],
                "title": track["title"],
                "artist": track["artist"]["name"],
                "cover_art": track["album"]["cover_medium"],
                "preview_url": track["preview"],
            })

        source = "deezer"

        if not candidates:
            itunes_response = await client.get(
                "https://itunes.apple.com/search",
                params={"term": q, "media": "music", "limit": 10},
            )
            itunes_data = itunes_response.json()

            for track in itunes_data.get("results", []):
                candidates.append({
                    "id": track["trackId"],
                    "title": track["trackName"],
                    "artist": track["artistName"],
                    "cover_art": track["artworkUrl100"],
                    "preview_url": track["previewUrl"],
                })

            source = "itunes"

    return {"query": q, "source": source, "candidates": candidates}
