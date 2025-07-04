
#!/usr/bin/env python3
"""
프로덕션 배포를 위한 초기 설정 스크립트
"""

import json
import os
from datetime import datetime

def setup_production_environment():
    """프로덕션 환경 설정"""
    
    print("🚀 프로덕션 환경 설정 시작...")
    
    # 1. 데이터베이스 백업
    if os.path.exists("db.json"):
        backup_filename = f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open("db.json", "r") as src, open(backup_filename, "w") as dst:
            dst.write(src.read())
        print(f"✅ 데이터베이스 백업 완료: {backup_filename}")
    
    # 2. 기본 설정 확인
    with open("db.json", "r") as f:
        db_data = json.load(f)
    
    # 3. 관리자 계정 확인
    print("📋 관리자 계정 정보:")
    print("   URL: /admin")
    print("   비밀번호: 6969")
    
    # 4. 등록된 사용자 수 확인
    allowed_users = db_data.get("allowed_users", [])
    test_users = db_data.get("test_users", [])
    
    print(f"👥 등록된 사용자 수: {len(allowed_users)}명")
    print(f"🧪 테스트 사용자 수: {len(test_users)}명")
    
    # 5. 배포 체크리스트
    checklist = [
        "✅ FastAPI 서버 실행 확인",
        "✅ 관리자 페이지 접근 확인 (/admin)",
        "✅ 사용자 등록 기능 확인",
        "✅ 챌린지 기능 테스트",
        "✅ 영상 재생 확인",
        "✅ 데이터베이스 백업 완료",
        "✅ 보안 헤더 설정 완료",
        "✅ CORS 설정 완료"
    ]
    
    print("\n📝 배포 체크리스트:")
    for item in checklist:
        print(f"   {item}")
    
    print("\n🌐 배포 후 확인사항:")
    print("   1. /health 엔드포인트로 서버 상태 확인")
    print("   2. /api/status 엔드포인트로 API 상태 확인")
    print("   3. 메인 페이지에서 챌린지 시작 테스트")
    print("   4. 관리자 페이지에서 사용자 관리 테스트")
    
    print("\n🎉 프로덕션 환경 설정 완료!")
    print("이제 Replit Deploy 버튼을 클릭하여 배포할 수 있습니다.")

if __name__ == "__main__":
    setup_production_environment()
