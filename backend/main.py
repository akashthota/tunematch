import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from urllib.parse import quote
from audio_analysis import analyze_track
from database import init_db

init_db()

load_dotenv()

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

app = FastAPI(title="TuneMatch API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/recommendations")
async def get_recommendations(artist: str, track: str, limit: int = 10):
    async with httpx.AsyncClient() as client:
        # Step 1: seed track's tags + seed artist's similar artists
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
        seed_tags = [t["name"].lower() for t in tags_response.json().get("toptags", {}).get("tag", [])][:10]

        similar_response = await client.get(
            "https://ws.audioscrobbler.com/2.0/",
            params={
                "method": "artist.getSimilar",
                "artist": artist,
                "api_key": LASTFM_API_KEY,
                "format": "json",
            },
        )
        similar_artists = similar_response.json().get("similarartists", {}).get("artist", [])[:8]

        # Step 1b: resolve the seed track on Deezer to get its own audio features
        seed_deezer_response = await client.get(
            "https://api.deezer.com/search",
            params={"q": f"{artist} {track}"},
        )
        seed_deezer_tracks = seed_deezer_response.json().get("data", [])
        seed_audio = None
        if seed_deezer_tracks:
            seed_id = seed_deezer_tracks[0]["id"]
            seed_preview = seed_deezer_tracks[0]["preview"]
            seed_audio = await analyze_track(seed_id, "deezer", seed_preview)

        # Step 2: build candidate pool from each similar artist's top tracks on Deezer
        candidates = []
        for sim_artist in similar_artists:
            deezer_response = await client.get(
                "https://api.deezer.com/search",
                params={"q": sim_artist["name"]},
            )
            deezer_tracks = deezer_response.json().get("data", [])[:2]

            for dt in deezer_tracks:
                candidates.append({
                    "id": dt["id"],
                    "title": dt["title"],
                    "artist": dt["artist"]["name"],
                    "cover_art": dt["album"]["cover_medium"],
                    "preview_url": dt["preview"],
                    "similar_artist_match": float(sim_artist["match"]),
                })

        # Step 3: score each candidate
        scored = []
        for c in candidates:
            if c["artist"].lower() == artist.lower() and c["title"].lower() == track.lower():
                continue  # skip the seed track itself

            c_tags_response = await client.get(
                "https://ws.audioscrobbler.com/2.0/",
                params={
                    "method": "track.getTopTags",
                    "artist": c["artist"],
                    "track": c["title"],
                    "api_key": LASTFM_API_KEY,
                    "format": "json",
                },
            )
            c_tags = [t["name"].lower() for t in c_tags_response.json().get("toptags", {}).get("tag", [])][:10]

            tag_score = sum(
                (10 - i) for i, tag in enumerate(seed_tags) if tag in c_tags
            )
            similar_artist_score = c["similar_artist_match"] * 20
            same_artist_penalty = -15 if c["artist"].lower() == artist.lower() else 0

            # Audio similarity: only computed if both seed and candidate analyzed successfully
            audio_score = 0
            tempo_mismatch = False
            c_audio = await analyze_track(c["id"], "deezer", c["preview_url"])
            if seed_audio and c_audio:
                tempo_diff = abs(seed_audio["tempo"] - c_audio["tempo"])

                # Hard filter: tempo/feel is too different to be a genuine match,
                # regardless of tag or artist-similarity signals
                if tempo_diff > 40:
                    tempo_mismatch = True
                    audio_score = -25
                else:
                    tempo_score = max(0, 10 - tempo_diff / 5)

                    if max(seed_audio["energy"], c_audio["energy"]) > 0:
                        energy_ratio = min(seed_audio["energy"], c_audio["energy"]) / max(seed_audio["energy"], c_audio["energy"])
                    else:
                        energy_ratio = 0
                    energy_score = energy_ratio * 10

                    audio_score = tempo_score + energy_score

            total_score = tag_score + similar_artist_score + same_artist_penalty + audio_score

            scored.append({
                **{k: v for k, v in c.items() if k != "similar_artist_match"},
                "score": round(max(0, total_score), 2),
                "matched_tags": [t for t in seed_tags if t in c_tags],
                "audio_matched": c_audio is not None and seed_audio is not None,
                "tempo_mismatch": tempo_mismatch,
            })

        # Step 4: dedupe by artist+title, sort by score, cap at limit
        seen = set()
        deduped = []
        for c in sorted(scored, key=lambda x: x["score"], reverse=True):
            key = (c["artist"].lower(), c["title"].lower())
            if key not in seen:
                seen.add(key)
                deduped.append(c)

        # Step 5: build cross-platform search links
        for c in deduped[:limit]:
            search_term = quote(f"{c['artist']} {c['title']}")
            c["links"] = {
                "spotify": f"https://open.spotify.com/search/{search_term}",
                "apple_music": f"https://music.apple.com/search?term={search_term}",
                "youtube_music": f"https://music.youtube.com/search?q={search_term}",
            }

    return {
        "seed": {"artist": artist, "track": track, "tags": seed_tags, "audio": seed_audio},
        "recommendations": deduped[:limit],
    }


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