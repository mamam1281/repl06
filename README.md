
# 14일 챌린지 시스템

## 🚀 배포 가이드

### 1. 로컬 테스트
```bash
# 의존성 설치 및 데이터베이스 초기화
python setup_db.py

# 서버 실행
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

### 2. Replit 배포

1. **Deploy 버튼 클릭**
   - Replit 워크스페이스 상단의 "Deploy" 버튼 클릭
   - "Autoscale" 선택

2. **배포 설정**
   - Machine configuration: 1vCPU, 2 GiB RAM (기본값)
   - Max number of machines: 3 (기본값)
   - Primary domains: 원하는 도메인 이름 입력
   - Run command: `uvicorn main:app --host 0.0.0.0 --port 5000`

3. **Deploy 버튼 클릭하여 배포 완료**

### 3. 배포 후 확인사항

- **헬스체크**: `https://your-domain.replit.dev/health`
- **API 상태**: `https://your-domain.replit.dev/api/status`
- **관리자 페이지**: `https://your-domain.replit.dev/admin` (비밀번호: 6969)

## 📋 관리자 기능

### 사용자 관리
- 개별 사용자 추가
- CSV 파일 일괄 업로드
- 사용자 진행도 초기화
- 사용자 완전 삭제

### 모니터링
- 실시간 참여자 현황
- 단계별 진행률 분석
- 포인트 지급 현황

## 🎯 주요 기능

1. **14일 챌린지 시스템**
   - DAY 1: 가입 보상
   - DAY 2: 설문조사
   - DAY 3-6: 카드뉴스 열람
   - DAY 7: 영상 시청
   - DAY 8-14: 결제 챌린지

2. **포인트 시스템**
   - 즉시 보상 지급
   - 랜덤 보상 시스템
   - 누적 포인트 관리

3. **관리자 대시보드**
   - 사용자 관리
   - 진행도 모니터링
   - 상세 분석

## 🔧 기술 스택

- **Backend**: FastAPI, Python 3.9+
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Database**: JSON 파일 기반 경량 DB
- **Deploy**: Replit Autoscale

## 📞 지원

배포나 사용 중 문제가 발생하면 관리자에게 문의하세요.
