import csv
import uuid
from pathlib import Path

# csv파일 경로 -> backend/data/sessions.csv
DATA_PATH = Path(__file__).parent.parent / "data" / "sessions.csv"

# CSV 컬럼 순서 고정
FIELDNAMES = ["id", "name", "age", "gender"]

def get_all() -> list:
    """등록된 사용자 전체를 리스트로 반환"""
    # 파일 없으면 빈 리스트 반환
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def add_session(name: str, age: int, gender: str) -> dict:
    """신규 사용자를 CSV에 추가하고 생성된 사용자 정보 반환"""
    # 랜덤 8자리 ID 생성
    session = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "age": age,
        "gender": gender
    }

    # 기존 데이터 불러온 후 신규 사용자 추가
    existing = get_all()
    existing.append(session)

    # 폴더 없으면 생성 후 전체 다시 쓰기
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(existing)

    return session

def remove_session(session_id: str) -> None:
    """session_id와 일치하는 사용자를 CSV에서 제거"""
    if not DATA_PATH.exists():
        return

    # 삭제 대상 제외하고 나머지만 유지
    rows = [r for r in get_all() if r["id"] != session_id]

    with open(DATA_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)