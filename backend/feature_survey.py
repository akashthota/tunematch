import essentia.standard as es
import urllib.request
import httpx
import asyncio
import statistics

# Deezer genre IDs for a diverse spread (pop, rock, rap, electronic, r&b, k-pop-ish via search)
GENRE_QUERIES = [
    "pop hits 2026", "rock classics", "hip hop hits", "edm dance",
    "r&b soul", "k-pop", "indie folk", "jazz standards",
    "country hits", "metal", "latin pop", "lofi chill",
]

async def get_tracks():
    tracks = []
    async with httpx.AsyncClient() as client:
        for q in GENRE_QUERIES:
            resp = await client.get("https://api.deezer.com/search", params={"q": q})
            data = resp.json().get("data", [])[:8]  # 8 per genre query = ~96 total
            for t in data:
                tracks.append({
                    "title": t["title"],
                    "artist": t["artist"]["name"],
                    "preview": t["preview"],
                })
    return tracks


def analyze(preview_url):
    path = "temp_survey.mp3"
    urllib.request.urlretrieve(preview_url, path)
    loader = es.MonoLoader(filename=path)
    audio = loader()

    rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
    bpm, _, _, _, _ = rhythm_extractor(audio)
    energy = es.Energy()(audio) / len(audio)
    centroid = es.SpectralCentroidTime()(audio)
    danceability, _ = es.Danceability()(audio)

    return bpm, energy, centroid, danceability


async def main():
    tracks = await get_tracks()
    print(f"Fetched {len(tracks)} candidate tracks. Analyzing...\n")

    results = []
    for i, t in enumerate(tracks):
        try:
            bpm, energy, centroid, dance = analyze(t["preview"])
            results.append({
                "name": f"{t['artist']} - {t['title']}",
                "tempo": bpm, "energy": energy, "centroid": centroid, "dance": dance,
            })
            print(f"[{i+1}/{len(tracks)}] OK: {t['artist']} - {t['title']}")
        except Exception as e:
            print(f"[{i+1}/{len(tracks)}] FAILED: {t['artist']} - {t['title']} ({e})")

    print(f"\nSuccessfully analyzed {len(results)} tracks.\n")

    # Save full data to CSV for reference
    with open("feature_survey.csv", "w") as f:
        f.write("name,tempo,energy,centroid,danceability\n")
        for r in results:
            f.write(f'"{r["name"]}",{r["tempo"]:.2f},{r["energy"]:.6f},{r["centroid"]:.2f},{r["dance"]:.4f}\n')

    # Summary stats per feature
    for feat in ["tempo", "energy", "centroid", "dance"]:
        vals = [r[feat] for r in results]
        print(f"{feat.upper():<12} min={min(vals):.4f}  max={max(vals):.4f}  "
              f"mean={statistics.mean(vals):.4f}  stdev={statistics.stdev(vals):.4f}")

    # Correlation between danceability and tempo (sanity check: are they redundant?)
    def correlation(a, b):
        n = len(a)
        mean_a, mean_b = statistics.mean(a), statistics.mean(b)
        cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
        std_a = (sum((x - mean_a) ** 2 for x in a)) ** 0.5
        std_b = (sum((x - mean_b) ** 2 for x in b)) ** 0.5
        return cov / (std_a * std_b) if std_a and std_b else 0

    tempos = [r["tempo"] for r in results]
    energies = [r["energy"] for r in results]
    centroids = [r["centroid"] for r in results]
    dances = [r["dance"] for r in results]

    print(f"\nCorrelation tempo vs danceability: {correlation(tempos, dances):.3f}")
    print(f"Correlation energy vs danceability: {correlation(energies, dances):.3f}")
    print(f"Correlation centroid vs danceability: {correlation(centroids, dances):.3f}")
    print(f"Correlation tempo vs centroid: {correlation(tempos, centroids):.3f}")

asyncio.run(main())