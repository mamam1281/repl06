from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from replit import db
import random

# FastAPI 앱 인스턴스 생성
app = FastAPI()

# --- Pydantic 데이터 모델 정의 ---
# API 요청/응답 형식을 강제하여 실수를 방지합니다.
class IdentifyRequest(BaseModel):
    nickname: str

# --- API 엔드포인트 구현 ---

@app.get("/")
def read_root():
    # 서버가 살아있는지 확인하기 위한 기본 엔드포인트
    return {"status": "Onboarding API is running!"}

@app.post("/api/identify")
async def identify(req: IdentifyRequest):
    """
    사용자를 식별하고 온보딩 참여 자격을 검증합니다.
    첫 참여 시 상태를 초기화하고 즉시 보상을 지급합니다.
    """
    nickname = req.nickname

    # 1. 자격 검증: 허용된 사용자인지 확인
    if nickname not in db.get("allowed_users", ()):
        raise HTTPException(status_code=403, detail="참여 자격이 없는 사용자입니다.")

    # 2. 중복 참여 방지: 이미 참여한 사용자인지 확인
    if f"user:{nickname}:valid" in db:
        raise HTTPException(status_code=400, detail="이미 참여한 사용자입니다.")

    # 3. 신규 사용자 상태 DB에 생성
    db[f"user:{nickname}:valid"] = "1"
    db[f"user:{nickname}:points"] = 50
    db[f"user:{nickname}:stage_state"] = 1  # 1: 설문 단계
    db[f"user:{nickname}:survey_step"] = 0
    db[f"user:{nickname}:card_index"] = 0
    db[f"user:{nickname}:video_progress"] = 0
    db[f"user:{nickname}:spend_amount"] = 0
    db[f"user:{nickname}:spend_tier"] = 0

    # 4. 전역 통계 업데이트: 전체 참여자 수 1 증가
    stats = db.get("global_stats", {})
    stats["participants"] = stats.get("participants", 0) + 1
    db["global_stats"] = stats

    # 5. 성공 응답 반환
    return {
      "valid": True,
      "userId": nickname,
      "is_new": True,
      "points": 50,
      "stage_state": 1
    }