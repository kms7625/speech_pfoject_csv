from fastapi import APIRouter
from pydantic import BaseModel
from services.sessions_service import get_all, add_session, remove_session

router = APIRouter(prefix="/api/sessions")

# 사용자 등록
class SessionCreate(BaseModel):
    name: str
    age: int
    gender : str

@router.get("")
def get_sessions():
    # 등록된 사용자 전체 조회
    return {"status": "success",
            "sessions": get_all()}

@router.post("")
def create_session(body: SessionCreate):
    # 신규 사용자 등록
    session = add_session(body.name,
                          body.age,
                          body.gender)
    return {"status": "success",
            "session": session
            }

# 삭제 API
@router.delete("/{session_id}")
def delete_session(session_id: str):
    remove_session(session_id)
    # 해당 사용자 임시저장 데이터도 삭제
    from services.score_service import delete_draft
    delete_draft(session_id)
    return {"status": "success",
            "data": {"deleted": session_id}}
