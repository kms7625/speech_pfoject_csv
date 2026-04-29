from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import questions # backend/routers/questions.py
from routers import sessions # bachend/routers/Session.py
from routers import score # bachend/routers/score.py
from routers import tts
from fastapi.staticfiles import StaticFiles # 정적 파일 서빙 추가


app = FastAPI(
    title="ADHD 체크리스트 API",
    version = "1,0,0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(questions.router) # backend/routers/questions.py
app.include_router(sessions.router) # bachend/routers/Session.py
app.include_router(score.router) # bachend/routers/score.py
app.include_router(tts.router)


static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static",
          StaticFiles(directory=str(static_dir)),
          name="static")


@app.get("/")
def root():
    return {"message": "ADHD 체크리스터 서버 동작 중"}