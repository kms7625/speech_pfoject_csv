import hashlib
from pathlib import Path
from gtts import gTTS

# 생성된 MP3 저장 폴더
TTS_DIR = Path(__file__).parent.parent / "static" / "tts"
TTS_DIR.mkdir(parents=True, exist_ok=True)

def _get_path(text: str, speed: float) -> Path:
    """텍스트 + 속도 조합으로 고유 파일명 생성 (중복 방지)"""
    key = f"{text}_{speed}".encode("utf-8")
    file_hash = hashlib.md5(key).hexdigest()[:16]
    return TTS_DIR / f"{file_hash}.mp3"

def generate(text: str, speed: float = 1.0) -> str:
    """TTS MP3 생성. 이미 있으면 재생성 안 함. 파일명 반환"""
    path = _get_path(text, speed)

    if not path.exists():
        # 0.7 이하면 gTTS slow 모드 적용
        slow = speed <= 0.7
        tts = gTTS(text=text, lang="ko", slow=slow)
        tts.save(str(path))

    return path.name

def get_file_path(filename: str) -> Path:
    """파일명으로 실제 경로 반환"""
    return TTS_DIR / filename