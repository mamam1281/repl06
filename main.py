# main.py
import os
import re
import random
from contextlib import asynccontextmanager
# ✅ 올바른 코드
from fastapi import FastAPI, HTTPException, Request
from starlette.responses import FileResponse
from pydantic import BaseModel
import database as db


# Lifespan Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    db.load_db()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)


# --- Pydantic 데이터 모델 ---
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
    progress: int


class SpendRequest(BaseModel):
    userId: str
    amount: int


# --- 보상 설정 ---
REWARD_TIERS = [{
    "threshold": 400000,
    "points": 1500,
    "tier": 6
}, {
    "threshold": 300000,
    "points": 2000,
    "tier": 5
}, {
    "threshold": 200000,
    "points": 1500,
    "tier": 4
}, {
    "threshold": 150000,
    "points": 1000,
    "tier": 3
}, {
    "threshold": 100000,
    "points": 500,
    "tier": 2
}, {
    "threshold": 50000,
    "points": 200,
    "tier": 1
}]

# ===================================================================
# === API 엔드포인트 ===
# ===================================================================


@app.post("/api/identify")
async def identify(req: IdentifyRequest):
    nickname = req.nickname
    if not re.match(r'^[a-zA-Z0-9\-_]+$', nickname) or len(nickname) > 50:
        raise HTTPException(status_code=400, detail="닉네임 형식 오류")
    if nickname not in db.get("allowed_users", []):
        raise HTTPException(status_code=403, detail="참여 자격 없음")
    if db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=400, detail="이미 참여함")

    db.set(f"user:{nickname}:valid", "1")
    db.set(f"user:{nickname}:points", 50)
    db.set(f"user:{nickname}:stage_state", 1)
    db.set(f"user:{nickname}:survey_step", 0)
    db.set(f"user:{nickname}:card_index", 0)
    db.set(f"user:{nickname}:video_progress", 0)
    db.set(f"user:{nickname}:spend_amount", 0)
    db.set(f"user:{nickname}:spend_tier", 0)
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


@app.post("/api/survey")
async def survey(req: SurveyRequest):
    nickname = req.userId
    question_id = req.questionId
    if not db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=403, detail="미인증 사용자")
    current_step = db.get(f"user:{nickname}:survey_step", 0)
    if current_step != question_id - 1:
        raise HTTPException(status_code=400, detail="잘못된 설문 순서")

    points_awarded = random.randint(10, 20)
    is_final_question = (question_id == 3)
    if is_final_question: points_awarded += random.randint(20, 50)

    total_points = db.get(f"user:{nickname}:points", 0) + points_awarded
    db.set(f"user:{nickname}:points", total_points)
    db.set(f"user:{nickname}:survey_step", current_step + 1)
    if is_final_question: db.set(f"user:{nickname}:stage_state", 2)
    return {
        "points_awarded": points_awarded,
        "total_points": total_points,
        "is_final": is_final_question
    }


@app.post("/api/cardview")
async def cardview(req: CardViewRequest):
    nickname = req.userId
    saved_idx = db.get(f"user:{nickname}:card_index", 0)
    if req.cardIndex <= saved_idx:
        return {
            "points_awarded": 0,
            "total_points": db.get(f"user:{nickname}:points", 0)
        }
    points = 5 if req.cardIndex < 4 else 20
    db.set(f"user:{nickname}:card_index", req.cardIndex)
    total_points = db.get(f"user:{nickname}:points", 0) + points
    db.set(f"user:{nickname}:points", total_points)
    if req.cardIndex == 4: db.set(f"user:{nickname}:stage_state", 3)
    return {"points_awarded": points, "total_points": total_points}


@app.post("/api/video")
async def video(req: VideoRequest):
    nickname = req.userId
    saved_progress = db.get(f"user:{nickname}:video_progress", 0)
    if req.progress <= saved_progress:
        return {
            "points_awarded": 0,
            "total_points": db.get(f"user:{nickname}:points", 0)
        }
    points = 10 if req.progress == 50 else 50
    db.set(f"user:{nickname}:video_progress", req.progress)
    total_points = db.get(f"user:{nickname}:points", 0) + points
    db.set(f"user:{nickname}:points", total_points)
    if req.progress == 100: db.set(f"user:{nickname}:stage_state", 4)
    return {"points_awarded": points, "total_points": total_points}


@app.post("/api/spend")
async def spend(req: SpendRequest):
    nickname = req.userId
    total_spend = db.get(f"user:{nickname}:spend_amount", 0) + req.amount
    db.set(f"user:{nickname}:spend_amount", total_spend)
    current_tier = db.get(f"user:{nickname}:spend_tier", 0)
    points_to_add = 0
    for tier_info in REWARD_TIERS:
        if total_spend >= tier_info["threshold"] and current_tier < tier_info[
                "tier"]:
            points_to_add = tier_info["points"]
            db.set(f"user:{nickname}:spend_tier", tier_info["tier"])
            break
    total_points = db.get(f"user:{nickname}:points", 0)
    if points_to_add > 0:
        total_points += points_to_add
        db.set(f"user:{nickname}:points", total_points)
    return {
        "points_awarded": points_to_add,
        "total_spend": total_spend,
        "total_points": total_points
    }


# --- 웹페이지 및 정적 파일 제공 ---
@app.get("/{path:path}")
async def serve_static_or_index(path: str):
    file_path = os.path.join(".", path)
    if path == "" or not os.path.exists(file_path) or os.path.isdir(file_path):
        return FileResponse("index.html")
    return FileResponse(file_path)
