import csv
import uuid
from pathlib import Path

# csv파일 경로 -> backend/data/children.csv
DATA_PATH = Path(__file__).parent.parent / "data" / "children.csv"

# CSV 컬럼 순서 고정
FIELDNAMES = ["id", "name", "age", "gender"]

def get_all() -> list:
    """등록된 아동 전체를 리스트로 반환"""
    # 파일 없으면 빈 리스트 반환
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def add_child(name: str, age: int, gender: str) -> dict:
    """새 아동을 CSV에 추가하고 생성된 아동 정보 반환"""
    # 랜덤 8자리 ID 생성
    child = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "age": age,
        "gender": gender
    }

    # 기존 데이터 불러온 후 새 아동 추가
    existing = get_all()
    existing.append(child)

    # 폴더 없으면 생성 후 전체 다시 쓰기
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(existing)

    return child

def remove_child(child_id: str) -> None:
    """child_id와 일치하는 아동을 CSV에서 제거"""
    if not DATA_PATH.exists():
        return

    # 삭제 대상 제외하고 나머지만 유지
    rows = [r for r in get_all() if r["id"] != child_id]

    with open(DATA_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)