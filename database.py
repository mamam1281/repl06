
import psycopg2
import psycopg2.extras
import json
import os
from threading import Lock
from contextlib import contextmanager

_lock = Lock()

@contextmanager
def get_db_connection():
    """PostgreSQL 연결 컨텍스트 매니저"""
    conn = None
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL 환경 변수가 설정되지 않았습니다. Replit Database를 먼저 생성해주세요.")
        
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def init_database():
    """데이터베이스 테이블 초기화"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # 사용자 데이터 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                key VARCHAR(255) PRIMARY KEY,
                value JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 전역 설정 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS global_settings (
                key VARCHAR(255) PRIMARY KEY,
                value JSONB NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 초기 데이터 설정
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
        
        for key, value in initial_data.items():
            cur.execute("""
                INSERT INTO global_settings (key, value) 
                VALUES (%s, %s) 
                ON CONFLICT (key) DO NOTHING
            """, (key, json.dumps(value)))

def load_db():
    """데이터베이스 초기화 (FastAPI 시작시 호출)"""
    try:
        init_database()
        print("✅ PostgreSQL 데이터베이스가 성공적으로 초기화되었습니다.")
    except Exception as e:
        print(f"⚠️ 데이터베이스 초기화 실패: {e}")
        print("Replit에서 Database를 먼저 생성해주세요.")

def get(key, default=None):
    """데이터 조회"""
    with _lock:
        try:
            with get_db_connection() as conn:
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # 사용자 데이터 테이블에서 먼저 검색
                cur.execute("SELECT value FROM user_data WHERE key = %s", (key,))
                result = cur.fetchone()
                if result:
                    return result['value']
                
                # 전역 설정 테이블에서 검색
                cur.execute("SELECT value FROM global_settings WHERE key = %s", (key,))
                result = cur.fetchone()
                if result:
                    return result['value']
                
                return default
        except Exception as e:
            print(f"데이터 조회 실패 ({key}): {e}")
            return default

def set(key, value):
    """데이터 저장"""
    with _lock:
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # 사용자 데이터인지 전역 설정인지 구분
                if key.startswith('user:') or key in ['allowed_users', 'test_users', 'global_stats']:
                    table = 'global_settings' if key in ['allowed_users', 'test_users', 'global_stats'] else 'user_data'
                else:
                    table = 'user_data'
                
                cur.execute(f"""
                    INSERT INTO {table} (key, value, updated_at) 
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (key) DO UPDATE SET 
                        value = EXCLUDED.value,
                        updated_at = CURRENT_TIMESTAMP
                """, (key, json.dumps(value)))
                
        except Exception as e:
            print(f"데이터 저장 실패 ({key}): {e}")
            raise e

def exists(key):
    """키 존재 여부 확인"""
    with _lock:
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # 사용자 데이터 테이블에서 검색
                cur.execute("SELECT 1 FROM user_data WHERE key = %s", (key,))
                if cur.fetchone():
                    return True
                
                # 전역 설정 테이블에서 검색
                cur.execute("SELECT 1 FROM global_settings WHERE key = %s", (key,))
                return cur.fetchone() is not None
                
        except Exception as e:
            print(f"키 존재 확인 실패 ({key}): {e}")
            return False

def delete(key):
    """데이터 삭제"""
    with _lock:
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # 사용자 데이터 테이블에서 삭제
                cur.execute("DELETE FROM user_data WHERE key = %s", (key,))
                deleted = cur.rowcount > 0
                
                # 전역 설정 테이블에서 삭제
                if not deleted:
                    cur.execute("DELETE FROM global_settings WHERE key = %s", (key,))
                    deleted = cur.rowcount > 0
                
                return deleted
                
        except Exception as e:
            print(f"데이터 삭제 실패 ({key}): {e}")
            return False

def get_all_users():
    """모든 참여 사용자 목록 조회 (관리자용)"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT key FROM user_data WHERE key LIKE 'user:%:valid'")
            results = cur.fetchall()
            
            users = []
            for row in results:
                nickname = row['key'].split(':')[1]
                users.append(nickname)
            
            return users
    except Exception as e:
        print(f"사용자 목록 조회 실패: {e}")
        return []
