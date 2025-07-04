from replit import db
import json
from threading import Lock

_lock = Lock()

def load_db():
    """데이터베이스 초기화 (FastAPI 시작시 호출)"""
    try:
        # 초기 데이터 설정
        if "allowed_users" not in db:
            db["allowed_users"] = [
                "peter-a4t7", "joy-b5g8", "chris-c9h1", "tester-01",
                "t001", "t002", "t003"
            ]

        if "test_users" not in db:
            db["test_users"] = ["tester-01", "t001", "t002", "t003"]

        if "global_stats" not in db:
            db["global_stats"] = {
                "participants": 0,
                "total_points_awarded": 0,
                "video_viewers": 0,
                "card_finishers": 0
            }

        print("✅ Replit DB가 성공적으로 초기화되었습니다.")
    except Exception as e:
        print(f"⚠️ 데이터베이스 초기화 실패: {e}")

def get(key, default=None):
    """데이터 조회"""
    with _lock:
        try:
            return db.get(key, default)
        except Exception as e:
            print(f"데이터 조회 실패 ({key}): {e}")
            return default

def set(key, value):
    """데이터 저장"""
    with _lock:
        try:
            db[key] = value
        except Exception as e:
            print(f"데이터 저장 실패 ({key}): {e}")
            raise e

def exists(key):
    """키 존재 여부 확인"""
    with _lock:
        try:
            return key in db
        except Exception as e:
            print(f"키 존재 확인 실패 ({key}): {e}")
            return False

def delete(key):
    """데이터 삭제"""
    with _lock:
        try:
            if key in db:
                del db[key]
                return True
            return False
        except Exception as e:
            print(f"데이터 삭제 실패 ({key}): {e}")
            return False

def get_all_users():
    """모든 참여 사용자 목록 조회 (관리자용)"""
    try:
        users = []
        for key in db.keys():
            if key.endswith(":valid"):
                nickname = key.split(":")[1]
                users.append(nickname)
        return users
    except Exception as e:
        print(f"사용자 목록 조회 실패: {e}")
        return []