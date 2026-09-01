import { useState, useRef } from "react";
import { Search, Play, Pause } from "lucide-react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [query, setQuery] = useState("");
  const [candidates, setCandidates] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [seed, setSeed] = useState(null);
  const [nowPlaying, setNowPlaying] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResults([]);
    setCandidates([]);
    setSeed(null);

    try {
      const resolveRes = await fetch(
        `${API_BASE}/resolve?q=${encodeURIComponent(query)}`
      );
      const resolveData = await resolveRes.json();

      if (!resolveData.candidates || resolveData.candidates.length === 0) {
        setError("No matching track found. Try a different search.");
        setLoading(false);
        return;
      }

      setCandidates(resolveData.candidates.slice(0, 5));
    } catch (err) {
      console.error("Search error:", err);
      setError("Something went wrong. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSeed = async (track) => {
    setCandidates([]);
    setSeed(track);
    setLoading(true);
    setError(null);

    try {
      const recRes = await fetch(
        `${API_BASE}/recommendations?artist=${encodeURIComponent(track.artist)}&track=${encodeURIComponent(track.title)}`
      );
      const recData = await recRes.json();
      setResults(recData.recommendations || []);
    } catch (err) {
      console.error("Recommendations error:", err);
      setError("Something went wrong fetching recommendations.");
    } finally {
      setLoading(false);
    }
  };

  const handlePlayTrack = (track) => {
    if (nowPlaying?.id === track.id) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.play();
        setIsPlaying(true);
      }
      return;
    }
    setNowPlaying(track);
    setIsPlaying(true);
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">TuneMatch</div>
        <nav className="nav">
          <span className="nav-item active">Search</span>
        </nav>
      </aside>

      <main className="main">
        <form className="search-bar" onSubmit={handleSearch}>
          <Search size={18} className="search-icon" />
          <input
            type="text"
            placeholder="Song title, artist..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </form>

        <div className="results-area">
          {loading && (
            <div className="empty-state">
              <p>
                {candidates.length === 0 && !seed
                  ? "Searching..."
                  : "Finding tracks that sound like this..."}
              </p>
            </div>
          )}

          {error && !loading && (
            <div className="empty-state">
              <p>{error}</p>
            </div>
          )}

          {!loading && candidates.length > 0 && (
            <>
              <div className="seed-label">Which one did you mean?</div>
              <div className="candidate-list">
                {candidates.map((c) => (
                  <button
                    key={c.id}
                    className="candidate-row"
                    onClick={() => handleSelectSeed(c)}
                  >
                    <img src={c.cover_art} alt="" className="candidate-cover" />
                    <div className="candidate-text">
                      <div className="candidate-title">{c.title}</div>
                      <div className="candidate-artist">{c.artist}</div>
                    </div>
                  </button>
                ))}
              </div>
            </>
          )}

          {!loading && !error && candidates.length === 0 && results.length === 0 && (
            <div className="empty-state">
              <p>Search a song to find what sounds like it.</p>
            </div>
          )}

          {!loading && results.length > 0 && (
            <>
              {seed && (
                <div className="seed-section">
                  <div className="seed-label">Your search</div>
                  <div className="track-card seed-card">
                    <div className="track-cover-wrap">
                      <img src={seed.cover_art} alt="" className="track-cover" />
                      <button
                        className="track-play-btn"
                        onClick={() => handlePlayTrack(seed)}
                      >
                        {nowPlaying?.id === seed.id && isPlaying ? (
                          <Pause size={18} />
                        ) : (
                          <Play size={18} />
                        )}
                      </button>
                    </div>
                    <div className="track-title">{seed.title}</div>
                    <div className="track-artist">{seed.artist}</div>
                  </div>
                  <div className="seed-label results-label">Similar tracks</div>
                </div>
              )}
              <div className="results-shelf">
                {results.map((track) => (
                  <div className="track-card" key={track.id}>
                    <div className="track-cover-wrap">
                      <img src={track.cover_art} alt="" className="track-cover" />
                      <button
                        className="track-play-btn"
                        onClick={() => handlePlayTrack(track)}
                      >
                        {nowPlaying?.id === track.id && isPlaying ? (
                          <Pause size={18} />
                        ) : (
                          <Play size={18} />
                        )}
                      </button>
                    </div>
                    <div className="track-title">{track.title}</div>
                    <div className="track-artist">{track.artist}</div>
                    <div className="track-meta">
                      <span className="track-score">{track.score}</span>
                      <div className="track-links">
                        {track.links?.spotify && (
                          <a href={track.links.spotify} target="_blank" rel="noreferrer">
                            Spotify
                          </a>
                        )}
                        {track.links?.apple_music && (
                          <a href={track.links.apple_music} target="_blank" rel="noreferrer">
                            Apple
                          </a>
                        )}
                        {track.links?.youtube_music && (
                          <a href={track.links.youtube_music} target="_blank" rel="noreferrer">
                            YT
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </main>

      {nowPlaying && (
        <div className="player-bar">
          <div className="player-track-info">
            <img src={nowPlaying.cover_art} alt="" className="player-cover" />
            <div>
              <div className="player-title">{nowPlaying.title}</div>
              <div className="player-artist">{nowPlaying.artist}</div>
            </div>
          </div>
          <button
            className="player-play-btn"
            onClick={() => handlePlayTrack(nowPlaying)}
          >
            {isPlaying ? <Pause size={20} /> : <Play size={20} />}
          </button>
          {nowPlaying.preview_url && (
            <audio
              ref={audioRef}
              src={nowPlaying.preview_url}
              autoPlay
              onEnded={() => setIsPlaying(false)}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default App;