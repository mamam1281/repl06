
from fastapi import APIRouter
from datetime import datetime
import database as db

router = APIRouter()

@router.get("/health")
async def health_check():
    """배포 상태 확인용 헬스체크 엔드포인트"""
    try:
        # DB 연결 확인
        test_users = db.get("allowed_users", [])
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "registered_users": len(test_users),
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/api/status")
async def api_status():
    """API 상태 확인"""
    active_users = []
    allowed_users = db.get("allowed_users", [])
    
    for nickname in allowed_users:
        if db.exists(f"user:{nickname}:valid"):
            active_users.append(nickname)
    
    return {
        "api_version": "1.0.0",
        "total_registered": len(allowed_users),
        "active_participants": len(active_users),
        "endpoints_available": [
            "/api/identify",
            "/api/survey", 
            "/api/cardview",
            "/api/video",
            "/api/spend",
            "/admin"
        ]
    }
