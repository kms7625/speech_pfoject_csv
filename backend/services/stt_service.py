import uuid
from pathlib import Path
import whisper

# 업로드 음성 파일 임시 저장 폴더
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Whisper 모델 로딩 — 서버 시작 시 한 번만 실행
model = whisper.load_model("base")

def transcribe_audio(content: bytes) -> str:
    """음성 바이트 데이터를 텍스트로 변환해서 반환"""
    # 임시 파일로 저장 (Whisper는 파일 경로로 입력받음)
    file_id   = str(uuid.uuid4())[:8]
    save_path = UPLOAD_DIR / f"{file_id}.webm"

    with open(save_path, "wb") as f:
        f.write(content)

    # Whisper로 한국어 텍스트 변환
    result = model.transcribe(str(save_path), language="ko", fp16=False)
    text   = result["text"].strip()

    # 처리 완료 후 임시 파일 삭제
    save_path.unlink(missing_ok=True)

    return text