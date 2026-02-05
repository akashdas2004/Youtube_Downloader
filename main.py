from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import uuid
import os
import shutil

app = FastAPI()

TMP = "/tmp"

class DownloadReq(BaseModel):
    url: str
    type: str   # audio | video


@app.post("/download")
def download(req: DownloadReq):

    ytdlp_path = shutil.which("yt-dlp")

    if not ytdlp_path:
        raise HTTPException(500, "yt-dlp binary not found in PATH")

    uid = str(uuid.uuid4())
    base = os.path.join(TMP, uid)

    try:
        if req.type == "audio":

            out = base + ".mp3"

            cmd = [
                ytdlp_path,
                "--no-playlist",
                "-x",
                "--audio-format", "mp3",
                "-o", out,
                req.url
            ]

        elif req.type == "video":

            out = base + ".mp4"

            cmd = [
                ytdlp_path,
                "--no-playlist",
                "-f",
                "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", out,
                req.url
            ]

        else:
            raise HTTPException(400, "Invalid type")

        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if p.returncode != 0:
            raise HTTPException(
                500,
                f"yt-dlp failed:\n{p.stderr}"
            )

        if not os.path.exists(out):
            raise HTTPException(500, "File not created")

        return FileResponse(
            out,
            filename=os.path.basename(out),
            media_type="application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Server exception: {str(e)}")
