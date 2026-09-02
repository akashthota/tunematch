# v2 Build Plan: Audio-Aware Similarity + Caching

Goal: fix the "same genre bucket, wrong vibe" problem (e.g. Seoul City -> generic K-pop)
by analyzing real audio characteristics (tempo, energy, mood) instead of relying only on
Last.fm tags and artist-similarity metadata.

- [x] 1. Add a database (SQLite, `analyzed_tracks` table with track_id/source/tempo/energy/analyzed_at)
- [x] 2. Install and test Essentia (confirmed working on macOS ARM64 + Python 3.14 -
      real BPM/energy extracted from a live Deezer preview via test_essentia.py)
- [x] 3. Audio analysis endpoint/function (download preview, run Essentia, cache in DB) - tested standalone, cache-hit confirmed instant
- [ ] 4. Background processing (FastAPI BackgroundTasks so analysis doesn't block requests)
- [x] 5. Blend audio features into /recommendations scoring - verified working, all candidates audio_matched=true
- [x] 6. Test against the known problem case (Seoul City / Jennie) - confirmed working: tempo-mismatched K-pop tracks correctly demoted, tempo/vibe-appropriate non-K-pop tracks (Maroon 5, Ninho) now rank above them
- [ ] 7. Update docs

## Notes
- Essentia installed cleanly via `pip install essentia` (dev build 2.1b6.dev1438),
  confirmed working end-to-end against a real Deezer preview URL.
- librosa fallback was scoped but not needed.

## Post-v6 refinement (same session, driven by real user testing)

After initial v2 completion, user testing revealed the K-pop clustering problem wasn't
fully solved — audio scoring was additive on top of tag/similar-artist score, which still
let same-scene tracks (e.g. BLACKPINK/JISOO/LISA for a Jennie seed) outrank genuinely
better audio matches. Root-caused and fixed through several iterations:

- [x] Added spectral centroid (brightness) as a third audio feature, after surveying 96
      tracks across genres to validate feature reliability. Danceability was tested and
      dropped (weak/counterintuitive signal, low correlation with other features).
      Energy kept but down-weighted (ENERGY_WEIGHT=0.3) due to its own unreliability
      (doesn't track perceived loudness/intensity well).
- [x] **Bug found and fixed**: initial similarity math used cosine similarity, which
      measures vector angle, not distance — broke down because all features normalize to
      positive-only ranges (same "octant" problem), so it failed to meaningfully separate
      tracks with very different raw values. Replaced with normalized Euclidean distance
      converted to a 0-1 similarity score. Verified via manual vector math before and
      after the fix.
- [x] **Bug found and fixed**: Last.fm sometimes returns collaboration-credit artist names
      (e.g. "Rosé, Bruno Mars") in similar-artists lists; searching Deezer for these
      literal strings returns junk (remixes/piano renditions/mashups) instead of real
      tracks. Now skipped (any similar-artist name containing a comma).
- [x] Removed tag_score and similar_artist_score from the ranking formula entirely — they
      still influence which artists' tracks enter the candidate pool, but audio_similarity
      is now the sole ranking signal within that pool (plus a same-artist penalty).
      This was necessary because tag/artist score alone was enough to keep poor audio
      matches (e.g. Kill This Love, 49% audio similarity) ranked above much better audio
      matches (e.g. Priceless by Maroon 5, 85% audio similarity).
- [x] Added a second candidate-sourcing path: Deezer search using the seed's own top 3
      Last.fm tags as search terms, in addition to similar-artist search. This breaks the
      "candidate pool = artist-scene graph only" bottleneck that was structurally limiting
      diversity, especially for K-pop seeds (K-pop's similar-artist graph is unusually
      insular due to label/group relationships and fandom scrobble behavior).
- [x] Added a per-artist cap (max 2 tracks per artist) in final results, to prevent one
      artist cluster from crowding out variety even within a now-more-diverse pool.
- [x] Frontend: added a percentage-based "sound match" badge (three-tier color coding)
      replacing the earlier binary tempo-mismatch flag, to surface the real continuous
      audio_similarity score to the user.

Result: re-testing Jennie/Seoul City after all changes returned Taylor Swift, Maroon 5,
Sting, Harry Styles, and Ninho ranked above all but one K-pop track (down from near-total
K-pop dominance originally). Known remaining limitation: tag-based candidate sourcing
can pull in candidates via noisy/unexpected Last.fm tags (e.g. "Peter", "English" as
literal tags on Seoul City) rather than genuinely meaningful genre labels — audio
similarity still filters honestly on top of whatever the noisy pool contains, but pool
composition itself isn't fully clean.

## Still open / deferred
- Step 4 (background processing) - deferred; synchronous analysis accepted as tradeoff
  so audio features affect same-request results, not just future cached requests.
- Local recommendation index (candidate sourcing independent of any external metadata,
  purely from a growing self-hosted library of audio-analyzed tracks) - discussed as the
  most complete long-term fix for candidate diversity, scoped as a distinct future effort,
  not built this session.
