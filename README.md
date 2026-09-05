# TuneMatch

Song similarity recommender. Give it a song, get back similar tracks — ranked by real audio
similarity (tempo, energy, brightness), not just genre tags — with cover art, a 30-second
preview you can play, and links to open each track on Spotify / Apple Music / YouTube Music.

No login, no account-connecting, no paid APIs.

## Status

v1 complete and functional end-to-end. v2 (audio-aware similarity via Essentia) is also
built and integrated. See `docs/BUILD_PLAN.md` and `docs/BUILD_PLAN_V2.md` for the full
step-by-step history, and `docs/TuneMatch_PRD.pdf` for the original product requirements.

## How it works

1. Search a song by title/artist — resolved via Deezer (iTunes as fallback)
2. If multiple tracks match, pick the right one from a disambiguation list
3. Backend builds a pool of candidate tracks from Last.fm's similar-artist data and
   genre-tag search, analyzes each candidate's audio with Essentia (tempo, energy,
   spectral brightness), and ranks them by real audio similarity to your chosen track
4. Results show cover art, a "% sound match" badge, and platform search links

## Structure

- `backend/` — FastAPI app (Python 3, httpx, SQLite, Essentia)
- `frontend/` — React app (Vite, custom black/matcha design system)
- `docs/` — PRD + build plans (v1 and v2)

## Local development

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/` (see `.env.example`) with your own Last.fm API key:

Get a free key at https://www.last.fm/api/account/create

Run the server:
```bash
uvicorn main:app --reload
```
Backend runs at `http://127.0.0.1:8000`. Interactive API docs at `/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`.

Both need to be running at the same time for the app to work.

## Tech stack

- **Backend**: Python, FastAPI, httpx (async HTTP), SQLite, Essentia (audio analysis)
- **Frontend**: React (Vite), plain CSS
- **Data sources**: Deezer (search, previews, cover art), iTunes (fallback), Last.fm (tags,
  similar artists)