import csv
import uuid
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/children")

# csv파일 경로 -> backend/data/children.csv
DATA_PATH = Path(__file__).parent.parent / "data" / "children.csv"

# 아동 등록할때 받을 데이터 형태
class ChildCreate(BaseModel):
    name: str
    age: int
    gender : str

def load_children() -> list:
    # csv파일없으면 빈 리스트 반환
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_child(child: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["id", "name", "age", "gender"]

    # 기존 데이터 읽기
    existing = []
    if DATA_PATH.exists() and DATA_PATH.stat().st_size > 0:
        with open(DATA_PATH, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            # 헤더가 올바른 경우만 읽기
            if reader.fieldnames == fieldnames:
                existing = list(reader)

    # 새 데이터 추가
    existing.append(child)

    # 전체 다시 쓰기 (헤더 한 번만)
    with open(DATA_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing)

@router.get("")
def get_children():
    # 등록된 아동 전체 조회
    return {"status": "success",
            "children": load_children()}

@router.post("")
def create_child(body: ChildCreate):
    # 새 아동 등록
    child = {
        "id": str(uuid.uuid4())[:8], # 랜덤 8자리 ID생성
        "name": body.name,
        "age": body.age,
        "gender": body.gender
    }
    save_child(child)
    return {"status": "success",
            "child": child
            }

# 삭제 API
@router.delete("/{child_id}")
def delete_child(child_id: str):
    if not DATA_PATH.exists():
        return {"status": "error", "message": "아동을 찾을 수 없습니다"}

    fieldnames = ["id", "name", "age", "gender"]

    # 기존 데이터 읽기
    with open(DATA_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r["id"] != child_id]

    # 삭제된 결과 전체 다시 쓰기 (헤더 한 번만)
    with open(DATA_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {"status": "success", "data": {"deleted": child_id}}
