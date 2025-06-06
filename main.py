from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from replit import db
import random
import time
import os
from security_headers import SecurityHeadersMiddleware

# FastAPI 앱 인스턴스 생성 (보안 설정 포함)
app = FastAPI(
    title="온보딩 챌린지 API",
    description="경량 온보딩 & 점진 누적 결제 유도 시스템",
    version="1.0.0",
    docs_url="/docs" if os.getenv("DEBUG", "False").lower() == "true" else None,
    redoc_url=None
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.replit.dev",
        "https://*.replit.app",
        "http://localhost:5000",
        "http://127.0.0.1:5000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 미들웨어
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*.replit.dev", "*.replit.app", "localhost", "127.0.0.1"]
)

# 보안 헤더 미들웨어
app.add_middleware(SecurityHeadersMiddleware)

# 요청 제한을 위한 간단한 레이트 리미터
request_counts = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    current_time = time.time()
    
    # IP별 요청 횟수 추적 (1분 단위)
    if client_ip not in request_counts:
        request_counts[client_ip] = []
    
    # 1분 이전 요청들 제거
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if current_time - req_time < 60
    ]
    
    # 분당 100회 제한
    if len(request_counts[client_ip]) >= 100:
        raise HTTPException(status_code=429, detail="요청 한도를 초과했습니다.")
    
    request_counts[client_ip].append(current_time)
    response = await call_next(request)
    return response

# --- 보안 유틸리티 함수 ---
def sanitize_input(text: str) -> str:
    """입력값 검증 및 정리"""
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="입력값이 비어있습니다.")
    
    # 길이 제한 (최대 50자)
    if len(text) > 50:
        raise HTTPException(status_code=400, detail="입력값이 너무 깁니다.")
    
    # 허용된 문자만 사용 (영문, 숫자, 하이픈, 언더스코어)
    import re
    if not re.match(r'^[a-zA-Z0-9\-_]+$', text):
        raise HTTPException(status_code=400, detail="허용되지 않은 문자가 포함되어 있습니다.")
    
    return text.strip()

def validate_user_access(nickname: str) -> bool:
    """사용자 접근 권한 검증"""
    if not nickname:
        return False
    
    allowed_users = db.get("allowed_users", ())
    return nickname in allowed_users

# --- Pydantic 데이터 모델 정의 ---
# API 요청/응답 형식을 강제하여 실수를 방지합니다.
class IdentifyRequest(BaseModel):
    nickname: str
    
    class Config:
        # 입력값 검증 설정
        str_strip_whitespace = True
        min_anystr_length = 1
        max_anystr_length = 50

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
    # 0. 입력값 보안 검증
    nickname = sanitize_input(req.nickname)

    # 1. 자격 검증: 허용된 사용자인지 확인
    if not validate_user_access(nickname):
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