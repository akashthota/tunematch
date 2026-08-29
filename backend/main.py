import httpx
from fastapi import FastAPI
import os
from dotenv import load_dotenv

load_dotenv()

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

app = FastAPI(title="TuneMatch API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/artist-info")
async def artist_info(artist: str, track: str):
    async with httpx.AsyncClient() as client:
        tags_response = await client.get(
            "https://ws.audioscrobbler.com/2.0/",
            params={
                "method": "track.getTopTags",
                "artist": artist,
                "track": track,
                "api_key": LASTFM_API_KEY,
                "format": "json",
            },
        )
        tags_data = tags_response.json()

        tags = [tag["name"] for tag in tags_data.get("toptags", {}).get("tag", [])][:10]

        similar_response = await client.get(
            "https://ws.audioscrobbler.com/2.0/",
            params={
                "method": "artist.getSimilar",
                "artist": artist,
                "api_key": LASTFM_API_KEY,
                "format": "json",
            },
        )
        similar_data = similar_response.json()

        similar_artists = [
            {"name": a["name"], "match": float(a["match"])}
            for a in similar_data.get("similarartists", {}).get("artist", [])
        ][:10]

    return {"artist": artist, "track": track, "tags": tags, "similar_artists": similar_artists}


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