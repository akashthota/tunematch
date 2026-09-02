import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from urllib.parse import quote
from audio_analysis import analyze_track, audio_similarity
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

@app.get("/debug-track-similar")
async def debug_track_similar(artist: str, track: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://ws.audioscrobbler.com/2.0/",
            params={
                "method": "track.getsimilar",
                "artist": artist,
                "track": track,
                "api_key": LASTFM_API_KEY,
                "format": "json",
            },
        )
        return response.json()

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

        # Step 2: build candidate pool from two sources —
        # (a) similar artists' tracks, (b) tracks matching the seed's own genre tags,
        # so the pool isn't entirely bottlenecked by artist-scene relationships
        candidates = []
        for sim_artist in similar_artists:
            if "," in sim_artist["name"]:
                continue  # skip collaboration-credit entries, unreliable for search
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

        for genre_tag in seed_tags[:3]:
            tag_deezer_response = await client.get(
                "https://api.deezer.com/search",
                params={"q": genre_tag},
            )
            tag_tracks = tag_deezer_response.json().get("data", [])[:4]

            for dt in tag_tracks:
                candidates.append({
                    "id": dt["id"],
                    "title": dt["title"],
                    "artist": dt["artist"]["name"],
                    "cover_art": dt["album"]["cover_medium"],
                    "preview_url": dt["preview"],
                    "similar_artist_match": 0.0,  # not artist-sourced, no artist-graph bonus
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

            same_artist_penalty = -15 if c["artist"].lower() == artist.lower() else 0

            # Audio similarity is now the primary ranking signal — tags/similar-artist
            # score are only used to source the candidate pool, not to rank within it
            c_audio = await analyze_track(c["id"], "deezer", c["preview_url"])
            audio_sim = audio_similarity(seed_audio, c_audio)
            audio_score = audio_sim * 100

            total_score = audio_score + same_artist_penalty

            scored.append({
                **{k: v for k, v in c.items() if k != "similar_artist_match"},
                "score": round(max(0, total_score), 2),
                "matched_tags": [t for t in seed_tags if t in c_tags],
                "audio_matched": c_audio is not None and seed_audio is not None,
                "audio_similarity": round(audio_sim, 3),
            })

        # Step 4: dedupe by artist+title, cap tracks per artist for variety, sort by score
        seen = set()
        artist_counts = {}
        deduped = []
        MAX_PER_ARTIST = 2
        for c in sorted(scored, key=lambda x: x["score"], reverse=True):
            key = (c["artist"].lower(), c["title"].lower())
            artist_key = c["artist"].lower()
            if key in seen:
                continue
            if artist_counts.get(artist_key, 0) >= MAX_PER_ARTIST:
                continue
            seen.add(key)
            artist_counts[artist_key] = artist_counts.get(artist_key, 0) + 1
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