import asyncio
from audio_analysis import analyze_track

FRESH_URL = "https://cdnt-preview.dzcdn.net/api/1/1/5/f/9/0/5f9a6a2ea1876e6d07c4b7feefa99951.mp3?hdnea=exp=1788333496~acl=/api/1/1/5/f/9/0/5f9a6a2ea1876e6d07c4b7feefa99951.mp3*~data=user_id=0,application_id=42~hmac=7ae8d3a4e2be6a4006b01ecd7449fe035ec78fc2558d18595130b64fe6a2598e"

async def main():
    result = await analyze_track(
        track_id="4091937401",
        source="deezer",
        preview_url=FRESH_URL,
    )
    print("First call (should analyze fresh):", result)

    result2 = await analyze_track(
        track_id="4091937401",
        source="deezer",
        preview_url=FRESH_URL,
    )
    print("Second call (should hit cache, instant):", result2)

asyncio.run(main())