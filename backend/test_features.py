import essentia.standard as es
import urllib.request

tracks = {
    "Seoul City (Jennie)": "https://cdnt-preview.dzcdn.net/api/1/1/c/b/c/0/cbcc7bdcb780249669d79f8ce4aba696.mp3?hdnea=exp=1788337246~acl=/api/1/1/c/b/c/0/cbcc7bdcb780249669d79f8ce4aba696.mp3*~data=user_id=0,application_id=42~hmac=091b468880a8b0bd3d8e70619ea635ac3f8c6a0fcb739c7cc2bc496787636aa3",
    "Kill This Love (BLACKPINK)": "https://cdnt-preview.dzcdn.net/api/1/1/5/e/e/0/5eea21e91507ec24e807eb93e9a61763.mp3?hdnea=exp=1788337247~acl=/api/1/1/5/e/e/0/5eea21e91507ec24e807eb93e9a61763.mp3*~data=user_id=0,application_id=42~hmac=6fcee18d06f986444ae6802982d2959ede6c655cfa6bc757572817dce9361216",
    "Ocean Eyes (Billie Eilish)": "https://cdnt-preview.dzcdn.net/api/1/1/0/2/3/0/0237a3ef9b4e0ed854fd69716497ca54.mp3?hdnea=exp=1788337453~acl=/api/1/1/0/2/3/0/0237a3ef9b4e0ed854fd69716497ca54.mp3*~data=user_id=0,application_id=42~hmac=f3b00e6f627387fb6f03d068893b4af882cfae2e6c27a6ef8630c472adb7a0dd",
    "Enter Sandman (Metallica)": "https://cdnt-preview.dzcdn.net/api/1/1/e/6/d/0/e6dd0ea47498689b3de69ac3e17a8746.mp3?hdnea=exp=1788337454~acl=/api/1/1/e/6/d/0/e6dd0ea47498689b3de69ac3e17a8746.mp3*~data=user_id=0,application_id=42~hmac=067d57ba135d54fed0b13dfd7c88711498ba8529c995f1fdd6f3db398af57f17",
    "One More Time (Daft Punk)": "https://cdnt-preview.dzcdn.net/api/1/1/f/8/c/0/f8c5dc3837912dba37c9a1ab3170cc3f.mp3?hdnea=exp=1788337454~acl=/api/1/1/f/8/c/0/f8c5dc3837912dba37c9a1ab3170cc3f.mp3*~data=user_id=0,application_id=42~hmac=19b68217189aa5d991f3f0a74148a943dd09c4f04ee3ae1e08b99758792411fa",
    "HUMBLE. (Kendrick Lamar)": "https://cdnt-preview.dzcdn.net/api/1/1/5/9/c/0/59c7208affd26e5d728f03dd312dc4cd.mp3?hdnea=exp=1788337454~acl=/api/1/1/5/9/c/0/59c7208affd26e5d728f03dd312dc4cd.mp3*~data=user_id=0,application_id=42~hmac=0a09e192d69023bec98028536eceb5103adabf4746ec6bd86aa8a32a4c6650fd",
    "Don't Know Why (Norah Jones)": "https://cdnt-preview.dzcdn.net/api/1/1/5/0/5/0/505ac2cc16183dd63353736a145d042f.mp3?hdnea=exp=1788337455~acl=/api/1/1/5/0/5/0/505ac2cc16183dd63353736a145d042f.mp3*~data=user_id=0,application_id=42~hmac=c7ab04a3c44d3a5e8a1fb4a1db283ab0c793ff3ef39c0bffd33679a4fc12ab2f",
}

results = []

for name, url in tracks.items():
    print(f"Analyzing: {name}...")
    path = "temp_compare.mp3"
    try:
        urllib.request.urlretrieve(url, path)
        loader = es.MonoLoader(filename=path)
        audio = loader()

        rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
        bpm, _, beats_confidence, _, _ = rhythm_extractor(audio)

        energy = es.Energy()(audio) / len(audio)
        centroid = es.SpectralCentroidTime()(audio)

        results.append((name, bpm, energy, centroid))
    except Exception as e:
        print(f"  FAILED: {e}")

print("\n" + "=" * 90)
print(f"{'Track':<32}{'Tempo':>10}{'Energy':>14}{'Centroid':>14}")
print("=" * 90)
for name, bpm, energy, centroid in results:
    print(f"{name:<32}{bpm:>10.2f}{energy:>14.6f}{centroid:>14.2f}")