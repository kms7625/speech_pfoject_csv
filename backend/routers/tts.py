from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel
from gtts import gTTS
import hashlib

router = APIRouter(prefix="/api/tts")

# 생성된 MP3 파일 저장 폴더
TTS_DIR =Path(__file__).parent.parent / "static" / "tts"
TTS_DIR.mkdir(parents=True,
              exist_ok=True)

class TTSRequest(BaseModel):
    text: str
    speed: float = 1.0 # 기본값 1.0 (0.5 ~ 2.0)

def get_tts_path(text: str, speed: float) -> Path:
    # 같은 텍스트는 같은 파일명 - 중복생성방지
    key = f"{text}_{speed}".encode("utf-8")
    file_hash = hashlib.md5(key).hexdigest()[:16]
    return TTS_DIR / f"{file_hash}.mp3"

@router.post("/generate")
def generate_tts_path(body: TTSRequest):
    path = get_tts_path(body.text, body.speed)

    # 이미 만든 파일이면 재생성 안함
    if not path.exists():
        # 0.7이하면 슬로우모드사용
        slow = body.speed <= 0.7
        tts = gTTS(text=body.text, lang="ko", slow=False)
        tts.save(str(path))

    # speed 값도 함께 반환 (프론트에서 playbackRate에 사용)
    return {"status": "success",
            "filename": path.name,
            "speed": body.speed}

@router.get("/file/{filename}")
def serve_tts_file(filename: str):
    path = TTS_DIR / filename
    if not path.exists():
        return {"status": "error",
                "message": "파일 없음"}
    return FileResponse(str(path), media_type="audio/mpeg")
