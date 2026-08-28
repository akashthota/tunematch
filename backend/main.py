from fastapi import FastAPI

app = FastAPI(title="TuneMatch API")


@app.get("/health")
def health_check():
    return {"status": "ok"}