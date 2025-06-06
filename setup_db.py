from replit import db

# 1. 참여 자격이 있는 사전 인증된 사용자 목록
db["allowed_users"] = ("peter-a4t7", "joy-b5g8", "chris-c9h1")

# 2. '사회적 증거'를 위한 전역 통계 데이터 초기화
db["global_stats"] = {
    "participants": 0,
    "total_points_awarded": 0,
    "video_viewers": 0,
    "card_finishers": 0
}

# 3. 테스트를 위해 기존에 생성된 모든 사용자 데이터를 삭제
keys_to_delete = [key for key in db.keys() if key.startswith("user:")]
for key in keys_to_delete:
    del db[key]

print("✅ Replit DB가 성공적으로 초기화되었습니다.")
print(f"허용된 사용자: {db['allowed_users']}")
print(f"초기 통계: {db['global_stats']}")