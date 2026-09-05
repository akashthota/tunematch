import urllib.request
import numpy as np

preview_url = "https://cdnt-preview.dzcdn.net/api/1/1/5/f/9/0/5f9a6a2ea1876e6d07c4b7feefa99951.mp3?hdnea=exp=1788583101~acl=/api/1/1/5/f/9/0/5f9a6a2ea1876e6d07c4b7feefa99951.mp3*~data=user_id=0,application_id=42~hmac=8cd17feee6fdbe5d85a9e427efa3be8cfab453676812751df21e30f38121132f"

path = "test_compare.mp3"
urllib.request.urlretrieve(preview_url, path)

print("=== librosa ===")
import librosa
audio, sr = librosa.load(path, sr=None, mono=True)
tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
tempo = np.atleast_1d(tempo)[0]
rms = librosa.feature.rms(y=audio)
energy = np.mean(rms)
centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
centroid_val = np.mean(centroid)
print(f"Tempo: {float(tempo):.2f}")
print(f"Energy: {float(energy):.6f}")
print(f"Centroid: {float(centroid_val):.2f}")

print("\n=== essentia ===")
import essentia.standard as es
loader = es.MonoLoader(filename=path)
audio_es = loader()
rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
bpm, _, _, _, _ = rhythm_extractor(audio_es)
raw_energy = es.Energy()(audio_es)
normalized_energy = raw_energy / len(audio_es)
centroid_es = es.SpectralCentroidTime()(audio_es)
print(f"Tempo: {bpm:.2f}")
print(f"Energy: {normalized_energy:.6f}")
print(f"Centroid: {centroid_es:.2f}")