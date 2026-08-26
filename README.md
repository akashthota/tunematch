# TuneMatch

Song similarity recommender. Give it a song, get back similar tracks with cover art, a
similarity reason, a 30-second preview, and links to open the track on Spotify / Apple Music /
YouTube Music.

No login, no account-connecting, no paid APIs.

## Status

v1 build in progress. See `docs/TuneMatch_PRD.pdf` for the full product requirements and
`docs/BUILD_PLAN.md` for the step-by-step commit plan.

## Structure

- `backend/` — FastAPI app (Python 3, httpx, pytest)
- `frontend/` — React app (Vite, plain CSS)
- `docs/` — PRD + build plan

## Local development

Backend and frontend setup instructions will be added as each piece comes online (steps 2 and 8
of the build plan).