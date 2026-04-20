import csv
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/score")

DATA_PATH = Path(__file__).parent.parent / "data" / "responses.csv"
# 임시저장 파일 경로
DRAFT_PATH = Path(__file__).parent.parent / "data" / "drafts.csv"

# 답변 1개의 형태 정의
class Answer(BaseModel):
    question_id: int # 문항 번호 (1~20)
    value: int       # 선택값 (0~3)

# 요청 전체 형태: 아동ID + 답변20개
class ScoreRequest(BaseModel):
    child_id: str
    answers: list[Answer]
    response_time: float

def calc_score(answers: list[Answer]) -> dict:
    # 1~9번 : 부주의 점수
    inattention = sum(a.value for a in answers
                      if 1 <= a.question_id <= 9)
    # 10~18번 : 과잉행동/충동성 점수
    hyperactivity = sum(a.value for a in answers
                        if 10 <= a.question_id <= 18)
    # 19~20번은 총점에만 포함
    total = sum(a.value for a in answers)

    return {
        "inattention": inattention,     # 부주의(0~27)
        "hyperactivity": hyperactivity, # 과잉행동(0~27)
        "total": total                  # 총점(0~54)
    }

def save_response(child_id: str, scores: dict, response_time: float) -> str:
    DATA_PATH.parent.mkdir(parents=True,
                           exist_ok=True)

    response_id = str(uuid.uuid4())[:8]
    row = {
        "response_id": response_id,
        "child_id": child_id,
        "inattention": scores["inattention"],
        "hyperactivity": scores["hyperactivity"],
        "total": scores["total"],
        "response_time": round(response_time, 2), # 초 단위
        "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    fieldnames = list(row.keys())
    # 파일이 없거나 비어있으면 헤더 작성
    write_header = not DATA_PATH.exists() or DATA_PATH.stat().st_size == 0

    with open(DATA_PATH, "a",
              newline="",
              encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    return response_id

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
    response_id = save_response(body.child_id, scores, body.response_time)

    return {
        "status": "success",
        "response_id": response_id,
        "scores": {
            "inattention": f"{scores['inattention']}/27",
            "hyperactivity": f"{scores['hyperactivity']}/27",
            "total": f"{scores['total']}/54"
        }
    }

@router.get("/history/{child_id}")
def get_history(child_id: str):
    # 특정 아동의 과거 검사 결과 전체 조회
    if not DATA_PATH.exists():
        return {"status": "success", "history": []}

    with open(DATA_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        history = [row for row in reader if row["child_id"] == child_id]

    return {"status": "success", "history": history}

@router.get("/admin/all")
def get_all_responses():
    if not DATA_PATH.exists():
        return {"status": "success", "data":[]}

    with open(DATA_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    return {"status": "success", "data": rows}

# 임시저장할 데이터 형태
class DraftRequest(BaseModel):
    child_id: str
    answers: list[Answer]  # 지금까지 답변한 것만

# 임시저장
@router.post("/draft/save")
def save_draft(body: DraftRequest):
    DRAFT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 기존 drafts에서 이 아동 것 제거 후 새로 저장
    existing = []
    if DRAFT_PATH.exists() and DRAFT_PATH.stat().st_size > 0:
        with open(DRAFT_PATH, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            # 같은 child_id 것만 제거
            existing = [r for r in reader if r["child_id"] != body.child_id]

    # 답변을 JSON 문자열로 직렬화해서 1행으로 저장
    import json
    row = {
        "child_id": body.child_id,
        "answers": json.dumps([{"question_id": a.question_id, "value": a.value}
                                for a in body.answers]),
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    existing.append(row)

    fieldnames = ["child_id", "answers", "saved_at"]
    with open(DRAFT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing)

    return {"status": "success", "saved_at": row["saved_at"]}

# 임시저장 불러오기
@router.get("/draft/{child_id}")
def load_draft(child_id: str):
    if not DRAFT_PATH.exists():
        return {"status": "success", "draft": None}

    import json
    with open(DRAFT_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["child_id"] == child_id:
                # JSON 문자열을 다시 리스트로 변환
                answers = json.loads(row["answers"])
                return {
                    "status": "success",
                    "draft": {
                        "answers": answers,
                        "saved_at": row["saved_at"]
                    }
                }

    return {"status": "success", "draft": None}

# 임시저장 삭제 (제출 완료 후 호출)
@router.delete("/draft/{child_id}")
def delete_draft(child_id: str):
    if not DRAFT_PATH.exists():
        return {"status": "success"}

    with open(DRAFT_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r["child_id"] != child_id]

    fieldnames = ["child_id", "answers", "saved_at"]
    with open(DRAFT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {"status": "success"}