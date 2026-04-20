from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel
from services.tts_service import generate, get_file_path

router = APIRouter(prefix="/api/tts")

# tts 생성 요청 형태
class TTSRequest(BaseModel):
    text: str
    speed: float = 1.0 # 기본값 1.0 (0.5 ~ 2.0)


# tts mp3 파일 생성(이미 있으면 재사용)
@router.post("/generate")
def generate_tts(body: TTSRequest):
    filename = generate(body.text, body.speed)
    # speed 값도 함께 반환 (프론트에서 playbackRate에 사용)
    return {"status": "success",
            "filename": filename,
            "speed": body.speed}

# 생성된 mp3 파일 서빙
@router.get("/file/{filename}")
def serve_file(filename: str):
    path = get_file_path(filename)
    if not path.exists():
        return {"status": "error",
                "message": "파일 없음"}
    return FileResponse(str(path), media_type="audio/mpeg")
