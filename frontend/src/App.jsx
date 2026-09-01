import { useState } from "react";
import { Search, Play, Pause } from "lucide-react";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [nowPlaying, setNowPlaying] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    // wiring to backend comes in step 9/10 — placeholder for now
    console.log("searching for:", query);
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
          {results.length === 0 && !loading && (
            <div className="empty-state">
              <p>Search a song to find what sounds like it.</p>
            </div>
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
            onClick={() => setIsPlaying(!isPlaying)}
          >
            {isPlaying ? <Pause size={20} /> : <Play size={20} />}
          </button>
        </div>
      )}
    </div>
  );
}

export default App;