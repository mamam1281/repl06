# setup_db.py
import json

DB_FILE = "db.json"

# 초기 데이터 구조
initial_data = {
    # 1. 참여 자격이 있는 사전 인증된 사용자 목록
    "allowed_users": [
        "peter-a4t7",
        "joy-b5g8",
        "chris-c9h1"
    ],
    # 2. '사회적 증거'를 위한 전역 통계 데이터 초기화
    "global_stats": {
        "participants": 0,
        "total_points_awarded": 0,
        "video_viewers": 0,
        "card_finishers": 0
    }
}

# db.json 파일 생성
with open(DB_FILE, "w") as f:
    json.dump(initial_data, f, indent=4)

print(f"✅ '{DB_FILE}' 파일이 성공적으로 생성되었습니다.")
print(f"허용된 사용자: {initial_data['allowed_users']}")
print(f"초기 통계: {initial_data['global_stats']}")