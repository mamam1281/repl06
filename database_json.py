
import json
import os
from threading import Lock
from contextlib import contextmanager

_lock = Lock()
DB_FILE = "db.json"

def init_database():
    """JSON 데이터베이스 파일 초기화"""
    if not os.path.exists(DB_FILE):
        initial_data = {
            "allowed_users": [
                "peter-a4t7", "joy-b5g8", "chris-c9h1", "tester-01",
                "t001", "t002", "t003"
            ],
            "test_users": ["tester-01", "t001", "t002", "t003"],
            "global_stats": {
                "participants": 0,
                "total_points_awarded": 0,
                "video_viewers": 0,
                "card_finishers": 0
            }
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)

def load_db():
    """데이터베이스 초기화 (FastAPI 시작시 호출)"""
    try:
        init_database()
        print("✅ JSON 데이터베이스가 성공적으로 초기화되었습니다.")
    except Exception as e:
        print(f"⚠️ JSON 데이터베이스 초기화 실패: {e}")

def _load_data():
    """JSON 파일에서 데이터 로드"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"JSON 파일 로드 실패: {e}")
        return {}

def _save_data(data):
    """JSON 파일에 데이터 저장"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"JSON 파일 저장 실패: {e}")
        raise e

def get(key, default=None):
    """데이터 조회"""
    with _lock:
        try:
            data = _load_data()
            return data.get(key, default)
        except Exception as e:
            print(f"데이터 조회 실패 ({key}): {e}")
            return default

def set(key, value):
    """데이터 저장"""
    with _lock:
        try:
            data = _load_data()
            data[key] = value
            _save_data(data)
        except Exception as e:
            print(f"데이터 저장 실패 ({key}): {e}")
            raise e

def exists(key):
    """키 존재 여부 확인"""
    with _lock:
        try:
            data = _load_data()
            return key in data
        except Exception as e:
            print(f"키 존재 확인 실패 ({key}): {e}")
            return False

def delete(key):
    """데이터 삭제"""
    with _lock:
        try:
            data = _load_data()
            if key in data:
                del data[key]
                _save_data(data)
                return True
            return False
        except Exception as e:
            print(f"데이터 삭제 실패 ({key}): {e}")
            return False

def get_all_users():
    """모든 참여 사용자 목록 조회 (관리자용)"""
    try:
        data = _load_data()
        users = []
        for key in data.keys():
            if key.startswith('user:') and key.endswith(':valid'):
                nickname = key.split(':')[1]
                users.append(nickname)
        return users
    except Exception as e:
        print(f"사용자 목록 조회 실패: {e}")
        return []
