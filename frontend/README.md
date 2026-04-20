# ADHD 체크리스트 (CSV 버전)

아동 등록 → 개인정보 동의 → 설문 진행 → 결과 확인 순서로 진행
TTS(문항 읽기), STT(음성 답변), 진행 상태 임시저장, 관리자 조회 기능을 포함

---

## 기술 스택

| 구분 | 기술 |
|---|---|
| 백엔드 | Python 3.12, FastAPI, Uvicorn |
| 프론트엔드 | Svelte 5, SvelteKit, Vite |
| TTS | gTTS |
| STT | OpenAI Whisper (local) |
| 데이터 저장 | CSV 파일 |

---

## 프로젝트 구조

```
speech_project_csv/
├── backend/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── routers/             # API 엔드포인트
│   │   ├── children.py
│   │   ├── questions.py
│   │   ├── score.py
│   │   ├── tts.py
│   │   └── stt.py
│   ├── services/            # 비즈니스 로직
│   │   ├── children_service.py
│   │   ├── questions_service.py
│   │   ├── score_service.py
│   │   ├── tts_service.py
│   │   └── stt_service.py
│   └── data/                # CSV 데이터 (자동 생성)
│       ├── children.csv
│       ├── responses.csv
│       └── drafts.csv
└── frontend/
    └── src/
        ├── routes/
        │   └── +page.svelte # 메인 UI
        └── lib/
            └── api.js       # API 호출 함수
```

---

## 설치 및 실행

### 사전 요구사항

- Python 3.10 이상
- Node.js 18 이상
- pip, npm

---

### 백엔드 설치

**Mac / Linux:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn python-multipart gtts openai-whisper
```

**Windows:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install fastapi uvicorn python-multipart gtts openai-whisper
```

> Whisper 모델(base, 약 140MB)은 첫 실행 시 자동 다운로드

---

### 프론트엔드 설치

```bash
cd frontend
npm install
```

---

### 실행

터미널 2개를 열어서 각각 실행

**터미널 1 — 백엔드:**

Mac / Linux:
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

Windows:
```bash
cd backend
.venv\Scripts\activate
uvicorn main:app --reload
```

**터미널 2 — 프론트엔드:**
```bash
cd frontend
npm run dev
```

백엔드: http://localhost:8000
프론트엔드: http://localhost:5173

---

## API 문서

백엔드 실행 후 http://localhost:8000/docs 에서 Swagger UI로 전체 API 확인 가능

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | /api/children | 아동 목록 조회 |
| POST | /api/children | 아동 등록 |
| DELETE | /api/children/{id} | 아동 삭제 |
| GET | /api/questions | 문항 + 선택지 조회 |
| POST | /api/score/submit | 답변 제출 + 채점 |
| GET | /api/score/history/{child_id} | 아동별 검사 이력 |
| GET | /api/score/admin/all | 전체 응답 조회 (관리자) |
| DELETE | /api/score/admin/delete | 응답 일괄 삭제 (관리자) |
| POST | /api/score/draft/save | 진행 상태 임시저장 |
| GET | /api/score/draft/{child_id} | 임시저장 불러오기 |
| DELETE | /api/score/draft/{child_id} | 임시저장 삭제 |
| POST | /api/tts/generate | TTS MP3 생성 |
| GET | /api/tts/file/{filename} | TTS 파일 서빙 |
| POST | /api/stt/transcribe | 음성 → 텍스트 변환 |

---

## 주요 기능

- 아동 등록 / 조회 / 삭제
- 개인정보 수집 동의 화면
- ADHD 체크리스트 20문항 (부주의 9문항 + 과잉행동 9문항 + 기타 2문항)
- TTS 문항 읽기 (재생 속도 0.5x ~ 2.0x 조절)
- STT 음성 답변 인식 (선택지 텍스트 및 "1번~4번" 번호 인식)
- 선택지 클릭/해제 기능
- 진행 상태 자동 임시저장 (선택 시마다 저장)
- 관리자 페이지 (전체 응답 조회, 문항별 응답 펼치기, 일괄 삭제)
- 점수 계산 (부주의 0~27점 / 과잉행동 0~27점 / 총점 0~54점)

---

## 데이터 파일

`backend/data/` 폴더에 CSV 파일로 저장. 첫 실행 시 자동 생성.

| 파일 | 내용 |
|---|---|
| children.csv | 아동 정보 (id, name, age, gender) |
| responses.csv | 검사 결과 (점수 + 문항별 응답 q1~q20) |
| drafts.csv | 진행 중 임시저장 데이터 |

> 개인정보 포함되는부분

---

## 주의사항

- STT는 로컬 Whisper 모델을 사용하므로 인터넷 연결 없이 동작함
- TTS는 gTTS를 사용하므로 인터넷 연결 필요함
- 마이크 사용을 위해 브라우저에서 마이크 권한 허용필수
- Chrome 또는 Edge 브라우저 사용 권장
