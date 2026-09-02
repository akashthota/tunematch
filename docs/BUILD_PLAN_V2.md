# v2 Build Plan: Audio-Aware Similarity + Caching

Goal: fix the "same genre bucket, wrong vibe" problem (e.g. Seoul City -> generic K-pop)
by analyzing real audio characteristics (tempo, energy, mood) instead of relying only on
Last.fm tags and artist-similarity metadata.

- [x] 1. Add a database (SQLite, `analyzed_tracks` table with track_id/source/tempo/energy/analyzed_at)
- [x] 2. Install and test Essentia (confirmed working on macOS ARM64 + Python 3.14 -
      real BPM/energy extracted from a live Deezer preview via test_essentia.py)
- [x] 3. Audio analysis endpoint/function (download preview, run Essentia, cache in DB) - tested standalone, cache-hit confirmed instant
- [ ] 4. Background processing (FastAPI BackgroundTasks so analysis doesn't block requests)
- [ ] 5. Blend audio features into /recommendations scoring
- [ ] 6. Test against the known problem case (Seoul City / Jennie)
- [ ] 7. Update docs

## Notes
- Essentia installed cleanly via `pip install essentia` (dev build 2.1b6.dev1438),
  confirmed working end-to-end against a real Deezer preview URL.
- librosa fallback was scoped but not needed.
