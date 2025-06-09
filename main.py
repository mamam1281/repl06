# main.py

import os
import re
import random
from contextlib import asynccontextmanager
from datetime import datetime, date, timezone
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
    day: int
    cardIndex: int


class VideoRequest(BaseModel):
    userId: str
    progress: int


class SpendRequest(BaseModel):
    userId: str
    amount: int


# --- 보상 설정 ---
REWARD_TIERS = [{
    "threshold": 50000,
    "points": 200,
    "tier": 1,
    "name": "5만원 달성"
}, {
    "threshold": 100000,
    "points": 500,
    "tier": 2,
    "name": "10만원 달성"
}, {
    "threshold": 150000,
    "points": 1000,
    "tier": 3,
    "name": "15만원 달성"
}, {
    "threshold": 200000,
    "points": 1500,
    "tier": 4,
    "name": "20만원 달성"
}, {
    "threshold": 300000,
    "points": 2000,
    "tier": 5,
    "name": "30만원 달성"
}, {
    "threshold": 400000,
    "points": 1500,
    "tier": 6,
    "name": "최종 달성"
}]


# --- 헬퍼 함수 ---
def _reset_user_progress(nickname: str):
    db.set(f"user:{nickname}:valid", "1")
    db.set(f"user:{nickname}:points", 5000)
    db.set(f"user:{nickname}:progression_day", 1)
    db.set(f"user:{nickname}:survey_step", 0)
    for i in range(3, 7):
        db.delete(f"user:{nickname}:viewed_cards_day_{i}")
    db.set(f"user:{nickname}:video_progress", 0)
    db.set(f"user:{nickname}:payment_log", {})
    db.set(f"user:{nickname}:spend_amount", 0)
    db.set(f"user:{nickname}:spend_tier", 0)
    db.delete(f"user:{nickname}:last_activity_date")


def record_mission_completion(nickname: str):
    db.set(f"user:{nickname}:last_activity_date",
           datetime.now(timezone.utc).isoformat())


# --- API 엔드포인트 ---
@app.post("/api/identify")
async def identify(req: IdentifyRequest):
    nickname = req.nickname
    if not re.match(r'^[a-zA-Z0-9\-_]+$', nickname) or len(nickname) > 50:
        raise HTTPException(status_code=400, detail="닉네임 형식 오류")
    if nickname not in db.get("allowed_users", []):
        raise HTTPException(status_code=403, detail="참여 자격 없음")
    is_test_user = nickname in db.get("test_users", [])
    if is_test_user:
        _reset_user_progress(nickname)
        return {
            "valid": True,
            "userId": nickname,
            "is_new": True,
            "points": 5000,
            "progression_day": 1,
            "is_test_user": True,
            "total_spend": 0,
            "current_tier": 0
        }
    if db.exists(f"user:{nickname}:valid"):
        last_activity_str = db.get(f"user:{nickname}:last_activity_date")
        progression_day = db.get(f"user:{nickname}:progression_day", 1)
        if last_activity_str:
            last_activity_date = datetime.fromisoformat(
                last_activity_str).date()
            today = datetime.now(timezone.utc).date()
            if today > last_activity_date:
                progression_day += 1
                db.set(f"user:{nickname}:progression_day", progression_day)
        return {
            "valid": True,
            "userId": nickname,
            "is_new": False,
            "points": db.get(f"user:{nickname}:points", 0),
            "progression_day": progression_day,
            "is_test_user": False,
            "total_spend": db.get(f"user:{nickname}:spend_amount", 0),
            "current_tier": db.get(f"user:{nickname}:spend_tier", 0)
        }
    _reset_user_progress(nickname)
    stats = db.get("global_stats", {})
    stats["participants"] = stats.get("participants", 0) + 1
    db.set("global_stats", stats)
    return {
        "valid": True,
        "userId": nickname,
        "is_new": True,
        "points": 5000,
        "progression_day": 1,
        "is_test_user": False,
        "total_spend": 0,
        "current_tier": 0
    }


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
    is_final_question = (question_id == 3)
    if is_final_question:
        points_awarded = random.choice([3000, 5000, 10000]) + 5000
        record_mission_completion(req.userId)
    total_points = db.get(f"user:{nickname}:points", 0) + points_awarded
    db.set(f"user:{nickname}:points", total_points)
    db.set(f"user:{nickname}:survey_step", current_step + 1)
    return {
        "points_awarded": points_awarded,
        "total_points": total_points,
        "is_final": is_final_question
    }


@app.post("/api/cardview")
async def cardview(req: CardViewRequest):
    nickname = req.userId
    if not db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=403, detail="미인증 사용자")
    progression_day = db.get(f"user:{nickname}:progression_day", 0)
    if not (3 <= req.day <= 6) or req.day > progression_day:
        raise HTTPException(status_code=403, detail="아직 열람할 수 없는 카드입니다.")
    viewed_cards_key = f"user:{nickname}:viewed_cards_day_{req.day}"
    viewed_cards = db.get(viewed_cards_key, [])
    if req.cardIndex in viewed_cards:
        return {
            "points_awarded": 0,
            "total_points": db.get(f"user:{nickname}:points", 0)
        }
    points_awarded = 5000
    total_points = db.get(f"user:{nickname}:points", 0) + points_awarded
    db.set(f"user:{nickname}:points", total_points)
    viewed_cards.append(req.cardIndex)
    db.set(viewed_cards_key, viewed_cards)
    if req.cardIndex == 3: record_mission_completion(req.userId)
    return {"points_awarded": points_awarded, "total_points": total_points}


@app.post("/api/video")
async def video(req: VideoRequest):
    nickname = req.userId
    if not db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=403, detail="미인증 사용자")
    progression_day = db.get(f"user:{nickname}:progression_day", 0)
    if progression_day != 7:
        raise HTTPException(status_code=400, detail="영상 시청은 7일차에만 진행할 수 있습니다.")
    saved_progress = db.get(f"user:{nickname}:video_progress", 0)
    if req.progress <= saved_progress:
        return {
            "points_awarded": 0,
            "total_points": db.get(f"user:{nickname}:points", 0)
        }
    points = 5000 if req.progress == 50 else 10000
    db.set(f"user:{nickname}:video_progress", req.progress)
    total_points = db.get(f"user:{nickname}:points", 0) + points
    db.set(f"user:{nickname}:points", total_points)
    if req.progress == 100: record_mission_completion(req.userId)
    return {"points_awarded": points, "total_points": total_points}


@app.post("/api/spend")
async def spend(req: SpendRequest):
    nickname = req.userId
    if not db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=403, detail="미인증 사용자")

    progression_day = db.get(f"user:{nickname}:progression_day", 0)
    if not (8 <= progression_day <= 14):
        raise HTTPException(status_code=400, detail="결제 챌린지 기간이 아닙니다.")

    # ▼▼▼ [수정] 테스트 유저 예외 조항을 삭제하여, 모든 유저에게 '하루 한 번' 규칙 적용 ▼▼▼
    last_activity_str = db.get(f"user:{nickname}:last_activity_date")
    if last_activity_str:
        last_activity_date = datetime.fromisoformat(last_activity_str).date()
        today = datetime.now(timezone.utc).date()
        if today == last_activity_date:
            current_spend = db.get(f"user:{nickname}:spend_amount", 0)
            new_spend = current_spend + req.amount
            db.set(f"user:{nickname}:spend_amount", new_spend)
            return {
                "message": "결제액이 추가로 기록되었습니다. 오늘의 보상은 이미 지급되었습니다.",
                "points_awarded": 0,
                "total_spend": new_spend,
                "current_tier": db.get(f"user:{nickname}:spend_tier", 0),
                "total_points": db.get(f"user:{nickname}:points", 0)
            }

    current_spend = db.get(f"user:{nickname}:spend_amount", 0)
    new_spend = current_spend + req.amount
    db.set(f"user:{nickname}:spend_amount", new_spend)

    current_tier_val = db.get(f"user:{nickname}:spend_tier", 0)
    points_to_add = 0

    next_tier_to_reach = None
    for tier in sorted(REWARD_TIERS, key=lambda x: x['tier']):
        if tier['tier'] > current_tier_val:
            next_tier_to_reach = tier
            break

    if next_tier_to_reach and new_spend >= next_tier_to_reach['threshold']:
        points_to_add = next_tier_to_reach['points']
        db.set(f"user:{nickname}:spend_tier", next_tier_to_reach['tier'])
        record_mission_completion(req.userId)

    total_points = db.get(f"user:{nickname}:points", 0) + points_to_add
    db.set(f"user:{nickname}:points", total_points)

    return {
        "message": "결제 활동이 성공적으로 기록되었습니다.",
        "points_awarded": points_to_add,
        "total_spend": new_spend,
        "current_tier": db.get(f"user:{nickname}:spend_tier", 0),
        "total_points": total_points
    }


@app.get("/api/reward-tiers")
async def get_reward_tiers():
    return REWARD_TIERS


@app.post("/api/nextday")
async def next_day(req: Request):
    body = await req.json()
    nickname = body.get("userId")
    if not db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=403, detail="미인증 사용자")
    if nickname not in db.get("test_users", []):
        raise HTTPException(status_code=403, detail="테스트 유저만 사용할 수 있는 기능입니다.")
    current_day = db.get(f"user:{nickname}:progression_day", 1)
    new_day = current_day + 1
    if new_day > 15: new_day = 15
    db.set(f"user:{nickname}:progression_day", new_day)
    db.delete(f"user:{nickname}:last_activity_date")
    return {"new_day": new_day}


@app.get("/{path:path}")
async def serve_static_or_index(path: str):
    file_path = os.path.join(".", path)
    if path == "" or not os.path.exists(file_path) or os.path.isdir(file_path):
        return FileResponse("index.html")
    return FileResponse(file_path)
