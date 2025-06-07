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


class VideoRequest(BaseModel):
    userId: str
    progress: int


class SpendRequest(BaseModel):
    userId: str
    day: int
    amount: int


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

    is_test_user = nickname in db.get("test_users", [])

    if db.exists(f"user:{nickname}:valid"):  # 재방문 사용자
        last_activity_str = db.get(f"user:{nickname}:last_activity_date")
        progression_day = db.get(f"user:{nickname}:progression_day", 1)

        if last_activity_str and not is_test_user:
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
            "is_test_user": is_test_user
        }

    # 신규 사용자 초기화
    db.set(f"user:{nickname}:valid", "1")
    db.set(f"user:{nickname}:points", 5000)
    db.set(f"user:{nickname}:progression_day", 1)
    db.set(f"user:{nickname}:survey_step", 0)
    db.set(f"user:{nickname}:viewed_cards", [])
    db.set(f"user:{nickname}:video_progress", 0)
    db.set(f"user:{nickname}:payment_log", {})

    stats = db.get("global_stats", {})
    stats["participants"] = stats.get("participants", 0) + 1
    db.set("global_stats", stats)

    return {
        "valid": True,
        "userId": nickname,
        "is_new": True,
        "points": 5000,
        "progression_day": 1,
        "is_test_user": is_test_user
    }


def record_mission_completion(nickname: str):
    db.set(f"user:{nickname}:last_activity_date",
           datetime.now(timezone.utc).isoformat())


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

    viewed_cards = db.get(f"user:{nickname}:viewed_cards", [])
    if req.day in viewed_cards:
        return {
            "points_awarded": 0,
            "total_points": db.get(f"user:{nickname}:points", 0)
        }

    points_awarded = 5000
    total_points = db.get(f"user:{nickname}:points", 0) + points_awarded
    db.set(f"user:{nickname}:points", total_points)

    viewed_cards.append(req.day)
    db.set(f"user:{nickname}:viewed_cards", viewed_cards)
    record_mission_completion(req.userId)

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

    if req.progress == 100:
        record_mission_completion(req.userId)

    return {"points_awarded": points, "total_points": total_points}


@app.post("/api/spend")
async def spend(req: SpendRequest):
    nickname = req.userId
    if not db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=403, detail="미인증 사용자")

    progression_day = db.get(f"user:{nickname}:progression_day", 0)
    if req.day != progression_day or not (8 <= req.day <= 14):
        raise HTTPException(status_code=400, detail="오늘의 결제 챌린지가 아닙니다.")

    log_key = f"user:{nickname}:payment_log"
    payment_log = db.get(log_key, {})
    payment_log[f"day_{req.day}"] = req.amount
    db.set(log_key, payment_log)

    points_awarded = 0
    special_reward = None

    if req.day in [8, 9, 10]:
        points_awarded = random.choice([5000, 15000, 20000, 30000])

    if req.day in [11, 12, 13] and req.amount >= 100000:
        points_awarded = random.randint(5000, 20000)

    if req.day == 14 and req.amount >= 100000:
        special_reward = "배민 상품권 3만원권"

    total_points = db.get(f"user:{nickname}:points", 0)
    if points_awarded > 0:
        total_points += points_awarded
        db.set(f"user:{nickname}:points", total_points)

    record_mission_completion(req.userId)

    return {
        "message": "결제 활동이 성공적으로 기록되었습니다. 관리자 확인 후 보상이 지급됩니다.",
        "points_awarded": points_awarded,
        "special_reward": special_reward,
        "total_points": total_points
    }


@app.post("/api/nextday")
async def next_day(req: Request):
    body = await req.json()
    nickname = body.get("userId")

    if not db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=403, detail="미인증 사용자")

    if nickname not in db.get("test_users", []):
        raise HTTPException(status_code=403, detail="테스트 유저만 사용할 수 있는 기능입니다.")

    current_day = db.get(f"user:{nickname}:progression_day", 1)

    # [수정] 14일차를 넘으면 2일차로 리셋 (무한 테스트)
    new_day = current_day + 1
    if new_day > 14:
        new_day = 2

    db.set(f"user:{nickname}:progression_day", new_day)

    return {"new_day": new_day}


@app.get("/{path:path}")
async def serve_static_or_index(path: str):
    file_path = os.path.join(".", path)
    if path == "" or not os.path.exists(file_path) or os.path.isdir(file_path):
        return FileResponse("index.html")
    return FileResponse(file_path)
