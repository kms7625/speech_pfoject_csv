from fastapi import APIRouter
from services.questions_service import get_questions_data, get_one_question

# 이 파일만의 라우터 객체 생성
# prefix: 이 파일의 모든 URL 앞에 자동으로 /api/questions 붙음
router = APIRouter(prefix="/api/questions")

@router.get("")
def get_questions():
    # 문장 + 선택지 반환
    data = get_questions_data()
    return {
        "status": "success",
        "questions": data["questions"],
        "options": data["options"]
    }

@router.get("/{question_id}")
def get_one(question_id: int):
    # 특정 번호 문항 하나만 반환
    result = get_one_question(question_id)
    if result is None:
        return {"status": "error",
                "message": f"{question_id}번 문항 없음"}
    return {"status": "success",
            "question": result["question"],
            "options": result["options"]}