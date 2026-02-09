import os
import subprocess
import tempfile

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import yt_dlp

app = FastAPI()

API_KEY = os.environ.get("API_KEY", "")

def require_key(key: str):
    if not API_KEY:
        return
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid key")

def get_stream_url(youtube_url: str) -> str:
    ydl_opts = {
        "quiet": True,
        "noplaylist": True,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info["url"]

@app.get("/frame")
def frame(
    url: str = Query(..., description="YouTube URL"),
    t: int = Query(..., ge=0, description="Time in whole seconds"),
    key: str = Query("", description="API key")
):
    require_key(key)

    stream_url = get_stream_url(url)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp_path = tmp.name
    tmp.close()

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-ss", str(t),
        "-i", stream_url,
        "-frames:v", "1",
        "-vf", "scale=iw:ih",
        "-y",
        tmp_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Failed to extract frame")

    return FileResponse(tmp_path, media_type="image/png", filename="frame.png")

@app.get("/")
def root():
    return {"ok": True, "hint": "Use /frame?url=...&t=90&key=..."}
