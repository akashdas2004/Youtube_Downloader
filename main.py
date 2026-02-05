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


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/download")
def download(req: DownloadReq):

    ytdlp_path = shutil.which("yt-dlp")

    if not ytdlp_path:
        raise HTTPException(status_code=500, detail="yt-dlp binary not found in PATH")

    uid = str(uuid.uuid4())
    base = os.path.join(TMP, uid)

    try:
        if req.type == "audio":

            out = base + ".mp3"

            cmd = [
                ytdlp_path,
                "--no-playlist",
                "--js-runtimes", "node",
                "--ffmpeg-location", "ffmpeg",
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
                "--js-runtimes", "node",
                "--ffmpeg-location", "ffmpeg",
                "-f",
                "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", out,
                req.url
            ]

        else:
            raise HTTPException(status_code=400, detail="Invalid type")

        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60 * 10
        )

        if p.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"yt-dlp failed:\n{p.stderr}"
            )

        if not os.path.exists(out):
            raise HTTPException(status_code=500, detail="File not created")

        return FileResponse(
            out,
            filename=os.path.basename(out),
            media_type="application/octet-stream"
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Download timed out")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server exception: {str(e)}")
