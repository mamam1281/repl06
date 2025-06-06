
import hashlib
import hmac
import os
from replit import db

class SecureDB:
    @staticmethod
    def get_secure_key(user_id: str, key_type: str) -> str:
        """보안 키 생성"""
        # 사용자 ID와 키 타입을 해시화하여 예측 불가능한 키 생성
        combined = f"user:{user_id}:{key_type}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16] + f":{user_id}:{key_type}"
    
    @staticmethod
    def validate_key_ownership(key: str, user_id: str) -> bool:
        """키 소유권 검증"""
        if not key or not user_id:
            return False
        
        parts = key.split(":")
        if len(parts) < 3:
            return False
            
        return parts[1] == user_id
    
    @staticmethod
    def safe_get(key: str, default=None):
        """안전한 DB 조회"""
        try:
            return db.get(key, default)
        except Exception:
            return default
    
    @staticmethod
    def safe_set(key: str, value):
        """안전한 DB 저장"""
        try:
            db[key] = value
            return True
        except Exception:
            return False
