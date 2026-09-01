# v1 Build Plan (incremental commits)

Tracking progress against PRD section 9.

- [x] 1. Repo scaffold + PRD
- [x] 2. Backend: FastAPI skeleton + health check endpoint
- [x] 3. Backend: Deezer/iTunes track resolution endpoint
- [x] 4. Backend: Last.fm tag + similar-artist integration
- [ ] 5. Backend: MusicBrainz integration
- [x] 6. Backend: ranking/scoring logic + /recommendations endpoint
- [x] 7. Backend: cross-platform search links (Odesli replaced - see deviations)
- [x] 8. Frontend: scaffold + search UI
- [ ] 9. Frontend: results list + preview player + platform links
- [ ] 10. Wire frontend to backend, end-to-end test
- [ ] 11. README + deployment docs
- [ ] 12. Deploy v1 (backend + frontend on free hosting tiers)

Later versions (v2+) get their own build plans once v1 is live.

## Deviations from PRD

- **Cross-platform links (step 7):** Odesli/song.link's free public API was discontinued
  (July 31, 2026) before this was built. Replaced with direct search-URL construction for
  Spotify, Apple Music, and YouTube Music instead of exact track-link resolution. No API call
  required, and no accuracy loss for well-known tracks — user gets one extra click on ambiguous
  matches.
- **MusicBrainz (step 5):** Deferred/skipped. Not used in the actual ranking formula (PRD
  section 6 only uses Last.fm tags + similar-artist data), so it added integration complexity
  without feeding the recommendation logic. Candidate for a v2 "artist relationships" feature.
