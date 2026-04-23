# 🧠 ADHD 체크리스트 웹 애플리케이션

아동 ADHD 증상 선별 검사를 위한 음성 기반 웹 애플리케이션

TTS(음성 출력)랑 STT(음성 인식)를 활용해 문항 읽어주고 음성으로 답변을 받음

---

## 📁 프로젝트 구조

```
speech_project_csv/
├── backend/                        # FastAPI 백엔드
│   ├── main.py                     # 앱 진입점, CORS 설정, 라우터 등록
│   ├── routers/
│   │   ├── children.py             # 아동 등록/삭제 API
│   │   ├── questions.py            # 문항/선택지 조회 API
│   │   ├── score.py                # 답변 제출/채점/임시저장/관리자 API
│   │   └── tts.py                  # TTS 음성 생성 API
│   ├── services/
│   │   ├── children_service.py     # 아동 데이터 CSV 처리
│   │   ├── questions_service.py    # 문항/선택지 데이터 정의
│   │   ├── score_service.py        # 채점, 응답 저장, 임시저장 로직
│   │   └── tts_service.py          # gTTS 음성 생성 및 캐싱
│   ├── data/                       # CSV 데이터 파일 (gitignore)
│   │   ├── children.csv            # 등록 아동 목록
│   │   ├── responses.csv           # 검사 응답 결과
│   │   └── drafts.csv              # 임시저장 데이터
│   └── static/
│       └── tts/                    # TTS 캐시 파일 (gitignore)
│
└── frontend/                       # SvelteKit 프론트엔드
    └── src/
        ├── routes/
        │   └── +page.svelte        # 메인 페이지 (전역 상태, phase 관리, TTS/STT 로직)
        └── lib/
            ├── api.js              # 백엔드 API 호출 함수 모음
            ├── stores.js           # 공유 유틸리티 (사운드, 자모분리, STT 매칭)
            └── components/
                ├── AdminModal.svelte   # 관리자 로그인 모달
                ├── SelectChild.svelte  # 아동 선택/등록 화면
                ├── Consent.svelte      # 개인정보 동의 화면
                ├── Checklist.svelte    # 체크리스트 카드형 화면
                ├── Admin.svelte        # 관리자 응답 조회 화면
                └── Result.svelte       # 검사 결과 화면
```

---

## ⚙️ 기술 스택

| 구분 | 기술 |
|------|------|
| 백엔드 | Python 3.12, FastAPI, gTTS |
| 프론트엔드 | SvelteKit, Svelte 5 (Runes) |
| 데이터 저장 | CSV 파일 |
| 음성 출력 (TTS) | gTTS (Google Text-to-Speech) |
| 음성 인식 (STT) | Web Speech API (브라우저 내장, 크롬 권장) |

---

## 🚀 실행 방법

### 백엔드

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

백엔드 서버: `http://localhost:8000`

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

프론트엔드 서버: `http://localhost:5173`

---

## 📋 주요 기능

### 검사 흐름
```
아동 선택 → 개인정보 동의 → 체크리스트 (20문항) → 결과 확인
```

### 체크리스트 화면
- 문항 카드형 UI (슬라이드 애니메이션)
- TTS 자동 재생 (문항 음성 출력)
- STT 자동 녹음 (TTS 재생 후 자동 시작)
- 음성 인식 성공 시 다음 문항 자동 이동
- 수동 선택지 클릭도 가능
- 진행률 바 + 문항 번호 표시
- 임시저장 (중단 후 이어하기 가능)

### STT 인식 방식
- 브라우저 내장 Web Speech API 사용 (크롬 전용)
- 한글 자모 분리 + 레벤슈타인 유사도 알고리즘으로 인식률 향상
- 인식 키워드: 전혀/아니(0점), 약간/가끔(1점), 꽤/자주(2점), 매우/항상(3점)
- 번호로도 답변 가능: 1번/2번/3번/4번

### 관리자 기능
- 관리자 인증 (ID: admin / PW: admin1234)
- 전체 응답 조회 테이블
- 문항별 답변 펼치기/접기
- 체크박스 선택 후 일괄 삭제

---

## 🗃️ 데이터 구조

### responses.csv 컬럼

| 컬럼                | 설명 |
|-------------------|------|
| response_id       | 응답 고유 ID (UUID 앞 8자리) |
| child_id          | 아동 ID |
| name              | 아동 이름 (저장 시점 기록) |
| age               | 아동 나이 (저장 시점 기록) |
| gender            | 아동 성별 (저장 시점 기록) |
| inattention(제외)   | 부주의 점수 (1~9번 문항 합산, 최대 27점) |
| hyperactivity(제외) | 과잉행동 점수 (10~18번 문항 합산, 최대 27점) |
| total             | 총점 (최대 54점) |
| response_time(제외) | 전체 응답 시간 (초) |
| avg_rt(미구현)       | 문항당 평균 반응시간 (초) |
| rt_std(미구현)       | 반응시간 표준편차 |
| fast_ratio(미구현)   | 충동성 비율 (%) |
| slow_ratio(미구현)   | 주의분산 비율 (%) |
| recorded_at       | 검사 일시 |
| q1 ~ q20          | 각 문항별 답변 (0~3) |

### 점수 해석

| 점수 | 의미 |
|------|------|
| 0점 | 전혀 그렇지 않다 |
| 1점 | 약간 그렇다 |
| 2점 | 꽤 그렇다 |
| 3점 | 매우 그렇다 |

---

## 🔧 설정 변경 방법

### 관리자 계정 변경
`frontend/src/lib/components/AdminModal.svelte`:
```js
const ADMIN_ID       = 'admin';
const ADMIN_PASSWORD = 'admin1234';
```

### STT 무음 대기 시간 변경
`frontend/src/routes/+page.svelte`:
```js
// 기본값 5000ms (5초)
silenceTimer = setTimeout(async () => { ... }, 5000);
```

### STT 인식 키워드 추가/수정
`frontend/src/lib/stores.js`:
```js
const KEYWORDS = [
    { value: 0, keywords: ["전혀", "아니", "없", "1번", "하나", "일번"] },
    { value: 1, keywords: ["약간", "조금", "가끔", "2번", "둘", "이번"] },
    { value: 2, keywords: ["꽤", "종종", "자주", "많", "3번", "셋", "삼번"] },
    { value: 3, keywords: ["매우", "항상", "심", "굉장", "4번", "넷", "사번", "매일"] }
];
```

### TTS 재생 속도 기본값 변경
`frontend/src/routes/+page.svelte`:
```js
let ttsSpeed = $state(1.0); // 0.5 ~ 2.0
```

---

## ⚠️ 주의사항

- STT는 **크롬 브라우저** 전용 (Web Speech API)
- 백엔드와 프론트엔드 **둘 다 실행** 필요
- `data/` 폴더의 CSV 파일은 gitignore 처리됨 → 처음 실행 시 자동 생성
- responses.csv 구조 변경 시 기존 파일 삭제 후 재생성 필요
- TTS 캐시 파일은 `backend/static/tts/`에 저장됨

---

## 📦 설치 필요 패키지

### 백엔드 (requirements.txt)
```
fastapi
uvicorn
gtts
python-dotenv
```

### 프론트엔드
```bash
npm install
```