# main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
import time
import os
import re

# 우리가 만든 모듈 임포트
import database as db
from security_headers import SecurityHeadersMiddleware

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="온보딩 챌린지 API",
    description="경량 온보딩 & 점진 누적 결제 유도 시스템",
    version="1.0.0",
    docs_url="/docs" if os.getenv("DEBUG", "False").lower() == "true" else None,
    redoc_url=None
)

# 서버 시작 시 db.json 로드
@app.on_event("startup")
def startup_event():
    db.load_db()

# --- 미들웨어 설정 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # MVP 단계에서는 편의상 모든 origin 허용
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"]) # MVP 단계에서는 편의상 모든 host 허용
app.add_middleware(SecurityHeadersMiddleware)

# --- Pydantic 데이터 모델 ---
class IdentifyRequest(BaseModel):
    nickname: str

# --- API 엔드포인트 ---
@app.get("/")
def read_root():
    return {"status": "Onboarding API is running!"}

@app.post("/api/identify")
async def identify(req: IdentifyRequest):
    nickname = req.nickname

    # 입력값 검증
    if not re.match(r'^[a-zA-Z0-9\-_]+$', nickname) or len(nickname) > 50:
        raise HTTPException(status_code=400, detail="닉네임 형식이 올바르지 않습니다.")

    # 자격 검증
    allowed_users = db.get("allowed_users", [])
    if nickname not in allowed_users:
        raise HTTPException(status_code=403, detail="참여 자격이 없는 사용자입니다.")

    # 중복 참여 방지
    if db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=400, detail="이미 참여한 사용자입니다.")

    # 신규 사용자 상태 생성
    db.set(f"user:{nickname}:valid", "1")
    db.set(f"user:{nickname}:points", 50)
    db.set(f"user:{nickname}:stage_state", 1)
    db.set(f"user:{nickname}:survey_step", 0)
    db.set(f"user:{nickname}:card_index", 0)
    db.set(f"user:{nickname}:video_progress", 0)
    db.set(f"user:{nickname}:spend_amount", 0)
    db.set(f"user:{nickname}:spend_tier", 0)

    # 전역 통계 업데이트
    stats = db.get("global_stats", {})
    stats["participants"] = stats.get("participants", 0) + 1
    db.set("global_stats", stats)

    return {
      "valid": True,
      "userId": nickname,
      "is_new": True,
      "points": 50,
      "stage_state": 1
    }