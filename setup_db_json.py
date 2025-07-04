
#!/usr/bin/env python3
# setup_db_json.py - JSON 데이터베이스 초기화 스크립트

import database_json as db

def main():
    print("🔄 JSON 데이터베이스 초기화 중...")
    
    try:
        # 데이터베이스 초기화
        db.load_db()
        
        # 초기 데이터 확인
        allowed_users = db.get("allowed_users", [])
        test_users = db.get("test_users", [])
        global_stats = db.get("global_stats", {})
        
        print(f"✅ JSON 데이터베이스가 성공적으로 초기화되었습니다.")
        print(f"📝 허용된 사용자: {allowed_users}")
        print(f"🧪 테스트 사용자: {test_users}")
        print(f"📊 초기 통계: {global_stats}")
        
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")

if __name__ == "__main__":
    main()
