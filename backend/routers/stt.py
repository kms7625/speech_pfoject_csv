from pathlib import Path
from fastapi import APIRouter, UploadFile, File
import whisper
import uuid

router = APIRouter(prefix="/api/stt")

# 업로드된 음성 파일 임시 저장 폴더
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Whisper 모델 로딩 (서버 시작 시 한번만)
model = whisper.load_model("base")

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # 업로드된 파일 저장
    file_id = str(uuid.uuid4())[:8]
    save_path = UPLOAD_DIR / f"{file_id}.webm"

    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Whisper로 텍스트 변환
    result = model.transcribe(str(save_path), language="ko", fp16=False)
    text = result["text"].strip()

    # 임시 파일 삭제
    save_path.unlink(missing_ok=True)

    return {"status": "success", "text": text}