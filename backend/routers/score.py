from fastapi import APIRouter
from pydantic import BaseModel
from services.score_service import (
    calc_score, save_response, get_history,
    get_all_responses, save_draft, load_draft, delete_draft,
    delete_responses
)

router = APIRouter(prefix="/api/score")

# 답변 1개의 형태 정의
class Answer(BaseModel):
    question_id: int # 문항 번호 (1~20)
    value: int       # 선택값 (0~3)

# 요청 전체 형태: 아동ID + 답변20개
class ScoreRequest(BaseModel):
    child_id: str
    answers: list[Answer]
    response_time: float

# 임시저장할 데이터 형태
class DraftRequest(BaseModel):
    child_id: str
    answers: list[Answer]  # 지금까지 답변한 것만

# 일괄 삭제 요청 형태
class DeleteRequest(BaseModel):
    response_ids: list[str]

@router.post("/submit")
def submit_answers(body: ScoreRequest):
    # 답변이 20개인지 확인
    if len(body.answers) != 20:
        return {
            "status": "error",
            "message": f"답변은 20개야합니다. 현재 {len(body.answers)}개"
        }

    # 각 선택값이 0~3 범위인지 확인
    for a in body.answers:
        if a.value not in (0, 1, 2, 3):
            return {
                "status": "error",
                "message": f"{a.question_id}번 문항의 값이 잘못됨: {a.value}"
            }

    scores = calc_score(body.answers)
    response_id = save_response(body.child_id,
                                scores,
                                body.response_time,
                                body.answers)

    return {
        "status": "success",
        "response_id": response_id,
        "scores": {
            "inattention":   scores['inattention'],
            "hyperactivity": scores['hyperactivity'],
            "total":         scores['total']
        }
    }

# 특정 아동의 과거 검사 결과 전체 조회
@router.get("/history/{child_id}")
def get_child_history(child_id: str):
   return {"status": "success",
           "history": get_history(child_id)}

@router.get("/latest/{child_id}")
def get_latest(child_id: str):
    """특정 아동의 가장 최근 검사 결과 반환"""
    from services.score_service import get_latest_response
    data = get_latest_response(child_id)
    if not data:
        return {"status": "none"}
    return {"status": "found", "data": data}

# 전체 응답 조회(관리자용)
@router.get("/admin/all")
def get_all():
    return {"status": "success",
            "data": get_all_responses()}

# 선택 응답 일괄 삭제(관리자용)
@router.delete("/admin/delete")
def delete_selected(body: DeleteRequest):
    delete_responses(body.response_ids)
    return {"status": "success",
            "deleted": len(body.response_ids)}

# 임시저장
@router.post("/draft/save")
def draft_save(body: DraftRequest):
    saved_at = save_draft(body.child_id, body.answers)
    return {"status": "success",
           "saved_at": saved_at}

# 임시저장 불러오기
@router.get("/draft/{child_id}")
def draft_load(child_id: str):
    draft = load_draft(child_id)
    return {"status": "success", "draft": draft}

# 임시저장 삭제 (제출 완료 후 호출)
@router.delete("/draft/{child_id}")
def draft_delete(child_id: str):
    delete_draft(child_id)
    return {"status": "success"}