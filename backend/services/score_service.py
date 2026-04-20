import csv
import json
import uuid
from datetime import datetime
from pathlib import Path

# 응답 결과 저장 파일
DATA_PATH  = Path(__file__).parent.parent / "data" / "responses.csv"
# 임시저장 파일
DRAFT_PATH = Path(__file__).parent.parent / "data" / "drafts.csv"
# 아동 정보 파일 (관리자 조회 시 조인용)
CHILD_PATH = Path(__file__).parent.parent / "data" / "children.csv"

def calc_score(answers) -> dict:
    """답변 리스트로 부주의/과잉행동/총점 계산"""
    # 1~9번: 부주의 (최대 27점)
    inattention   = sum(a.value for a in answers if 1 <= a.question_id <= 9)
    # 10~18번: 과잉행동/충동성 (최대 27점)
    hyperactivity = sum(a.value for a in answers if 10 <= a.question_id <= 18)
    # 전체 합산 (최대 54점)
    total         = sum(a.value for a in answers)
    return {"inattention": inattention,
            "hyperactivity": hyperactivity,
            "total": total}

def save_response(child_id: str, scores: dict,
                  response_time: float, answers: list) -> str:
    """채점 결과 + 문항별 응답을 responses.csv에 저장. response_id 반환"""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    response_id = str(uuid.uuid4())[:8]
    row = {
        "response_id":  response_id,
        "child_id":     child_id,
        "inattention":  scores["inattention"],
        "hyperactivity":scores["hyperactivity"],
        "total":        scores["total"],
        "response_time":round(response_time, 2),
        "recorded_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # q1~q20 각 문항 답변 개별 컬럼으로 추가
    for a in answers:
        row[f"q{a.question_id}"] = a.value

    # 파일 없거나 비어있으면 헤더 포함해서 새로 작성
    write_header = not DATA_PATH.exists() or DATA_PATH.stat().st_size == 0
    with open(DATA_PATH, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    return response_id

def get_history(child_id: str) -> list:
    """특정 아동의 검사 이력 전체 반환"""
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f)
                if r["child_id"] == child_id]

def get_all_responses() -> list:
    """전체 응답 조회 + children.csv 조인해서 이름/나이/성별 포함"""
    if not DATA_PATH.exists():
        return []

    # children.csv → {id: {name, age, gender}} 매핑
    child_map = {}
    if CHILD_PATH.exists():
        with open(CHILD_PATH, encoding="utf-8-sig") as f:
            for c in csv.DictReader(f):
                child_map[c["id"]] = {
                    "name":   c["name"],
                    "age":    c["age"],
                    "gender": c["gender"]
                }

    # responses.csv 읽고 아동 정보 합치기
    rows = []
    with open(DATA_PATH, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            info = child_map.get(row["child_id"], {})
            row["name"]   = info.get("name",   "알 수 없음")
            row["age"]    = info.get("age",    "-")
            row["gender"] = info.get("gender", "-")
            rows.append(row)
    return rows

def delete_responses(response_ids: list) -> None:
    """선택된 response_id 목록을 CSV에서 삭제"""
    if not DATA_PATH.exists():
        return
    with open(DATA_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        # 삭제 대상 제외
        rows = [r for r in reader
                if r["response_id"] not in response_ids]
        fieldnames = reader.fieldnames

    with open(DATA_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def save_draft(child_id: str, answers: list) -> str:
    """현재까지의 답변을 drafts.csv에 임시저장. saved_at 반환"""
    DRAFT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 같은 child_id 기존 데이터 제거
    existing = []
    if DRAFT_PATH.exists() and DRAFT_PATH.stat().st_size > 0:
        with open(DRAFT_PATH, encoding="utf-8-sig") as f:
            existing = [r for r in csv.DictReader(f)
                        if r["child_id"] != child_id]

    saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "child_id": child_id,
        # 답변 리스트를 JSON 문자열로 직렬화해서 1행에 저장
        "answers":  json.dumps([{"question_id": a.question_id,
                                  "value": a.value}
                                 for a in answers]),
        "saved_at": saved_at
    }
    existing.append(row)

    with open(DRAFT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f,
                    fieldnames=["child_id", "answers", "saved_at"])
        writer.writeheader()
        writer.writerows(existing)

    return saved_at

def load_draft(child_id: str) -> dict | None:
    """child_id의 임시저장 데이터 반환. 없으면 None"""
    if not DRAFT_PATH.exists():
        return None
    with open(DRAFT_PATH, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["child_id"] == child_id:
                return {
                    # JSON 문자열 → 리스트로 역직렬화
                    "answers":  json.loads(row["answers"]),
                    "saved_at": row["saved_at"]
                }
    return None

def delete_draft(child_id: str) -> None:
    """child_id의 임시저장 데이터 삭제"""
    if not DRAFT_PATH.exists():
        return
    with open(DRAFT_PATH, encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f)
                if r["child_id"] != child_id]

    with open(DRAFT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f,
                    fieldnames=["child_id", "answers", "saved_at"])
        writer.writeheader()
        writer.writerows(rows)