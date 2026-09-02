import essentia.standard as es

# We'll use a real Deezer preview URL to test end to end.
# This is Queen - Bohemian Rhapsody's preview from earlier testing.
preview_url = "https://cdnt-preview.dzcdn.net/api/1/1/5/f/9/0/5f9a6a2ea1876e6d07c4b7feefa99951.mp3?hdnea=exp=1788332329~acl=/api/1/1/5/f/9/0/5f9a6a2ea1876e6d07c4b7feefa99951.mp3*~data=user_id=0,application_id=42~hmac=9256ded61bea4da55f2594a295817153286fa5cd463d3a5ff122df3d32ead91c"

import urllib.request
print("Downloading preview...")
urllib.request.urlretrieve(preview_url, "test_preview.mp3")

print("Loading audio...")
loader = es.MonoLoader(filename="test_preview.mp3")
audio = loader()

print("Extracting tempo...")
rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
bpm, beats, beats_confidence, _, beats_intervals = rhythm_extractor(audio)

print("Extracting energy...")
energy = es.Energy()(audio)

print(f"BPM: {bpm}")
print(f"Beats confidence: {beats_confidence}")
print(f"Energy: {energy}")