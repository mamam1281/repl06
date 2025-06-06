# main.py
import os
import re
from fastapi import FastAPI, HTTPException, Request
# [수정 완료] FileResponse는 fastapi가 아닌 starlette.responses 에서 가져옵니다.
from starlette.responses import FileResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

# --- 우리가 만든 모듈 임포트 ---
import database as db

# --- 보안 헤더 미들웨어 클래스 ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # [수정 완료] 올바른 호출 방식
        response = await call_next(request)

        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none';"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

# --- FastAPI 앱 초기화 ---
app = FastAPI(
    title="온보딩 챌린지 API",
    description="경량 온보딩 & 점진 누적 결제 유도 시스템",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

# --- 서버 시작 이벤트 핸들러 ---
@app.on_event("startup")
def startup_event():
    db.load_db()

# --- 미들웨어 설정 ---
app.add_middleware(SecurityHeadersMiddleware)

# --- Pydantic 데이터 모델 ---
class IdentifyRequest(BaseModel):
    nickname: str

# ===================================================================
# === API 엔드포인트 ===
# ===================================================================

@app.post("/api/identify")
async def identify(req: IdentifyRequest):
    nickname = req.nickname

    if not re.match(r'^[a-zA-Z0-9\-_]+$', nickname) or len(nickname) > 50:
        raise HTTPException(status_code=400, detail="닉네임 형식이 올바르지 않습니다.")

    allowed_users = db.get("allowed_users", [])
    if nickname not in allowed_users:
        raise HTTPException(status_code=403, detail="참여 자격이 없는 사용자입니다.")

    if db.exists(f"user:{nickname}:valid"):
        raise HTTPException(status_code=400, detail="이미 참여한 사용자입니다.")

    db.set(f"user:{nickname}:valid", "1")
    db.set(f"user:{nickname}:points", 50)
    db.set(f"user:{nickname}:stage_state", 1)
    # ... (나머지 db.set 구문들)

    stats = db.get("global_stats", {})
    stats["participants"] = stats.get("participants", 0) + 1
    db.set("global_stats", stats)

    return {"valid": True, "userId": nickname, "is_new": True, "points": 50, "stage_state": 1}

# ===================================================================
# === 웹페이지 및 정적 파일 제공 (항상 맨 마지막에 위치해야 합니다) ===
# ===================================================================

@app.get("/{path:path}")
async def serve_static_or_index(path: str):
    file_path = os.path.join(".", path)
    if path == "" or not os.path.exists(file_path) or os.path.isdir(file_path):
        return FileResponse("index.html")
    return FileResponse(file_path)