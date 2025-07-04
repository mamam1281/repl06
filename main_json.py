
# main_json.py - JSON 데이터베이스 버전

import os
import re
import random
from contextlib import asynccontextmanager
from datetime import datetime, date, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
import database_json as db
from admin_json import setup_admin_routes
from health_check_json import router as health_router

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.load_db()
    yield

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 보안 헤더 미들웨어
app.add_middleware(SecurityHeadersMiddleware)

# 모델 정의
class IdentifyRequest(BaseModel):
    nickname: str

class SurveyRequest(BaseModel):
    userId: str
    questionId: int
    response: str

class CardViewRequest(BaseModel):
    userId: str
    cardIndex: int

class VideoRequest(BaseModel):
    userId: str
    currentTime: float
    duration: float
    isComplete: bool

class PayChallengeRequest(BaseModel):
    userId: str
    amount: int

# 정적 파일 서빙
@app.get("/")
async def serve_html():
    return FileResponse("index.html")

@app.get("/app.js")
async def serve_js():
    return FileResponse("app.js")

@app.get("/styles.css")
async def serve_css():
    return FileResponse("styles.css")

# 유틸리티 함수
def validate_nickname(nickname: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9\-_]{3,20}$', nickname))

def create_new_user(nickname: str):
    is_test_user = nickname in db.get("test_users", [])
    
    db.set(f"user:{nickname}:valid", True)
    db.set(f"user:{nickname}:points", 5000)
    db.set(f"user:{nickname}:progression_day", 1)
    db.set(f"user:{nickname}:survey_step", 0)
    db.set(f"user:{nickname}:viewed_cards", [])
    db.set(f"user:{nickname}:video_progress", 0)
    db.set(f"user:{nickname}:payment_activities", [])
    db.set(f"user:{nickname}:created_at", datetime.now(timezone.utc).isoformat())
    
    # 전체 참여자 수 증가
    global_stats = db.get("global_stats", {})
    global_stats["participants"] = global_stats.get("participants", 0) + 1
    global_stats["total_points_awarded"] = global_stats.get("total_points_awarded", 0) + 5000
    db.set("global_stats", global_stats)
    
    return {
        "userId": nickname, "is_new": True,
        "points": 5000, "progression_day": 1, "is_test_user": is_test_user
    }

def record_mission_completion(nickname: str):
    db.set(f"user:{nickname}:last_activity_date", datetime.now(timezone.utc).isoformat())

# API 엔드포인트
@app.post("/api/identify")
async def identify(req: IdentifyRequest):
    nickname = req.nickname.strip()
    
    if not validate_nickname(nickname):
        raise HTTPException(status_code=400, detail="올바르지 않은 닉네임 형식입니다.")
    
    allowed_users = db.get("allowed_users", [])
    if nickname not in allowed_users:
        raise HTTPException(status_code=403, detail="참여 자격이 없는 사용자입니다.")
    
    if db.exists(f"user:{nickname}:valid"):
        user_data = {
            "userId": nickname,
            "is_new": False,
            "points": db.get(f"user:{nickname}:points", 0),
            "progression_day": db.get(f"user:{nickname}:progression_day", 1),
            "is_test_user": nickname in db.get("test_users", [])
        }
        return user_data
    
    return create_new_user(nickname)

@app.post("/api/survey")
async def survey(req: SurveyRequest):
    nickname = req.userId
    question_id = req.questionId
    
    if not db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=403, detail="미인증 사용자")
    
    progression_day = db.get(f"user:{nickname}:progression_day", 0)
    if progression_day != 2:
        raise HTTPException(status_code=400, detail="설문은 2일차에만 진행할 수 있습니다.")
    
    current_step = db.get(f"user:{nickname}:survey_step", 0)
    if current_step != question_id - 1:
        raise HTTPException(status_code=400, detail="잘못된 설문 순서")
    
    survey_log_key = f"user:{nickname}:survey_responses"
    survey_log = db.get(survey_log_key, {})
    survey_log[f"question_{question_id}"] = req.response
    db.set(survey_log_key, survey_log)
    
    points_awarded = 0
    if question_id == 3:
        points_awarded = random.choice([3000, 5000, 10000]) + 5000
        record_mission_completion(req.userId)
    
    total_points = db.get(f"user:{nickname}:points", 0) + points_awarded
    db.set(f"user:{nickname}:points", total_points)
    db.set(f"user:{nickname}:survey_step", current_step + 1)
    
    return {
        "points_awarded": points_awarded,
        "total_points": total_points,
        "is_final": (question_id == 3)
    }

@app.post("/api/cardview")
async def cardview(req: CardViewRequest):
    nickname = req.userId
    card_index = req.cardIndex
    
    if not db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=403, detail="미인증 사용자")
    
    viewed_cards = db.get(f"user:{nickname}:viewed_cards", [])
    if card_index in viewed_cards:
        raise HTTPException(status_code=400, detail="이미 확인한 카드입니다.")
    
    viewed_cards.append(card_index)
    db.set(f"user:{nickname}:viewed_cards", viewed_cards)
    
    points_awarded = 5000 if card_index == 4 else 1000
    total_points = db.get(f"user:{nickname}:points", 0) + points_awarded
    db.set(f"user:{nickname}:points", total_points)
    
    if card_index == 4:
        record_mission_completion(nickname)
        global_stats = db.get("global_stats", {})
        global_stats["card_finishers"] = global_stats.get("card_finishers", 0) + 1
        db.set("global_stats", global_stats)
    
    return {
        "points_awarded": points_awarded,
        "total_points": total_points,
        "is_final": (card_index == 4)
    }

@app.post("/api/video")
async def video(req: VideoRequest):
    nickname = req.userId
    
    if not db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=403, detail="미인증 사용자")
    
    current_progress = db.get(f"user:{nickname}:video_progress", 0)
    
    if req.currentTime > req.duration:
        req.currentTime = req.duration
    
    progress_percentage = (req.currentTime / req.duration) * 100 if req.duration > 0 else 0
    points_awarded = 0
    total_points = db.get(f"user:{nickname}:points", 0)
    
    # 50% 시청 달성 (한 번만)
    if progress_percentage >= 50 and current_progress < 50:
        points_awarded += 2000
        total_points += 2000
    
    # 완전 시청 달성 (한 번만)
    if req.isComplete and current_progress < 100:
        points_awarded += 8000
        total_points += 8000
        record_mission_completion(nickname)
        
        global_stats = db.get("global_stats", {})
        global_stats["video_viewers"] = global_stats.get("video_viewers", 0) + 1
        db.set("global_stats", global_stats)
    
    db.set(f"user:{nickname}:video_progress", min(100, progress_percentage))
    db.set(f"user:{nickname}:points", total_points)
    
    return {
        "points_awarded": points_awarded,
        "total_points": total_points,
        "progress_percentage": progress_percentage,
        "is_complete": req.isComplete
    }

@app.post("/api/pay-challenge")
async def pay_challenge(req: PayChallengeRequest):
    nickname = req.userId
    amount = req.amount
    
    if not db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=403, detail="미인증 사용자")
    
    if amount < 10000:
        raise HTTPException(status_code=400, detail="최소 충전 금액은 10,000원입니다.")
    
    payment_activities = db.get(f"user:{nickname}:payment_activities", [])
    payment_record = {
        "amount": amount,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reward_claimed": False
    }
    payment_activities.append(payment_record)
    db.set(f"user:{nickname}:payment_activities", payment_activities)
    
    record_mission_completion(nickname)
    
    return {
        "success": True,
        "message": "결제 활동이 기록되었습니다. 관리자 확인 후 보상이 지급됩니다.",
        "amount": amount
    }

# 관리자 및 헬스체크 라우터 등록
setup_admin_routes(app, db)
app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
