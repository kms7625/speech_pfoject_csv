from fastapi import APIRouter
from pydantic import BaseModel
from services.Session_service import get_all, add_child, remove_child

router = APIRouter(prefix="/api/children")

# 아동 등록할때 받을 데이터 형태
class ChildCreate(BaseModel):
    name: str
    age: int
    gender : str

@router.get("")
def get_children():
    # 등록된 아동 전체 조회
    return {"status": "success",
            "children": get_all()}

@router.post("")
def create_child(body: ChildCreate):
    # 새 아동 등록
    child = add_child(body.name,
                      body.age,
                      body.gender)
    return {"status": "success",
            "child": child
            }

# 삭제 API
@router.delete("/{child_id}")
def delete_child(child_id: str):
    remove_child(child_id)
    # 해당 아동 임시저장 데이터도 삭제
    from services.score_service import delete_draft
    delete_draft(child_id)
    return {"status": "success",
            "data": {"deleted": child_id}}
