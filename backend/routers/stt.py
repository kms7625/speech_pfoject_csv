from fastapi import APIRouter, UploadFile, File
from services.stt_service import transcribe_audio

router = APIRouter(prefix="/api/stt")

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # 업로드된 파일 저장
    content = await file.read()
    text = transcribe_audio(content)
    return {"status": "success", "text": text}