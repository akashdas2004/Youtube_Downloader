from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import uuid
import os

app = FastAPI()

TMP = "/tmp"

class DownloadReq(BaseModel):
    url: str
    type: str   # audio | video

@app.post("/download")
def download(req: DownloadReq):

    uid = str(uuid.uuid4())
    base = os.path.join(TMP, uid)

    if req.type == "audio":

        out = base + ".mp3"

        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "-o", out,
            req.url
        ]

    elif req.type == "video":

        out = base + ".mp4"

        cmd = [
            "yt-dlp",
            "-f",
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", out,
            req.url
        ]

    else:
        raise HTTPException(400, "Invalid type")

    p = subprocess.run(cmd, capture_output=True)

    if p.returncode != 0:
        raise HTTPException(500, p.stderr.decode())

    if not os.path.exists(out):
        raise HTTPException(500, "File not created")

    return FileResponse(
        out,
        filename=os.path.basename(out),
        media_type="application/octet-stream"
    )
