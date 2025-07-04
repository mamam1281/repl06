

from fastapi import FastAPI, HTTPException, Form, File, UploadFile, Cookie, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import database as db
import csv
import io
from datetime import datetime

ADMIN_PASSWORD = "6969"

def setup_admin_routes(app):
    @app.get("/admin", response_class=HTMLResponse)
    async def admin_page(admin_session: str = Cookie(None)):
        if admin_session != ADMIN_PASSWORD:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>관리자 로그인</title>
                <meta charset="UTF-8">
                <style>
                    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
                    .login-container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
                    .login-title { text-align: center; margin-bottom: 30px; color: #333; font-size: 24px; font-weight: 600; }
                    .form-group { margin-bottom: 20px; }
                    .form-label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
                    .form-input { width: 100%; padding: 12px; border: 2px solid #e1e5e9; border-radius: 6px; font-size: 16px; transition: border-color 0.3s; }
                    .form-input:focus { outline: none; border-color: #667eea; }
                    .btn-login { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }
                    .btn-login:hover { transform: translateY(-2px); }
                </style>
            </head>
            <body>
                <div class="login-container">
                    <h1 class="login-title">🔐 관리자 로그인</h1>
                    <form action="/admin/login" method="post">
                        <div class="form-group">
                            <label class="form-label">비밀번호</label>
                            <input type="password" name="password" class="form-input" required placeholder="관리자 비밀번호를 입력하세요">
                        </div>
                        <button type="submit" class="btn-login">로그인</button>
                    </form>
                </div>
            </body>
            </html>
            """
        
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>챌린지 관리자 시스템</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; color: #1a202c; line-height: 1.6; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header-content { max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; }
                .header h1 { font-size: 28px; font-weight: 700; }
                .logout-btn { background: rgba(255,255,255,0.2); color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; }
                .logout-btn:hover { background: rgba(255,255,255,0.3); }
                .container { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .stat-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 4px solid #667eea; }
                .stat-number { font-size: 32px; font-weight: 700; color: #667eea; margin-bottom: 5px; }
                .stat-label { color: #64748b; font-size: 14px; font-weight: 500; }
                .section { background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; overflow: hidden; }
                .section-header { background: #f8fafc; padding: 20px; border-bottom: 1px solid #e2e8f0; }
                .section-title { font-size: 20px; font-weight: 600; color: #1a202c; margin-bottom: 5px; }
                .section-subtitle { color: #64748b; font-size: 14px; }
                .section-content { padding: 20px; }
                .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .form-group { margin-bottom: 20px; }
                .form-label { display: block; margin-bottom: 8px; color: #374151; font-weight: 500; font-size: 14px; }
                .form-input, .form-textarea { width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 14px; transition: border-color 0.3s; }
                .form-input:focus, .form-textarea:focus { outline: none; border-color: #667eea; }
                .form-textarea { resize: vertical; min-height: 120px; }
                .btn { padding: 12px 24px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.3s; display: inline-flex; align-items: center; gap: 8px; }
                .btn-primary { background: #667eea; color: white; }
                .btn-primary:hover { background: #5a67d8; transform: translateY(-1px); }
                .btn-secondary { background: #e5e7eb; color: #374151; }
                .btn-secondary:hover { background: #d1d5db; }
                .table-container { overflow-x: auto; }
                .table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
                .table th { background: #f8fafc; font-weight: 600; color: #374151; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
                .table tr:hover { background: #f8fafc; }
                .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
                .badge-success { background: #d1fae5; color: #065f46; }
                .badge-warning { background: #fef3c7; color: #92400e; }
                .badge-info { background: #dbeafe; color: #1e40af; }
                .badge-danger { background: #fee2e2; color: #991b1b; }
                .progress-bar { width: 100%; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }
                .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 4px; transition: width 0.3s; }
                .user-link { color: #667eea; text-decoration: none; font-weight: 500; }
                .user-link:hover { text-decoration: underline; }
                .loading { text-align: center; padding: 40px; color: #64748b; }
                .empty-state { text-align: center; padding: 60px 20px; color: #64748b; }
                .empty-icon { font-size: 48px; margin-bottom: 16px; }
                .tabs { display: flex; border-bottom: 1px solid #e5e7eb; margin-bottom: 20px; }
                .tab { padding: 12px 24px; border: none; background: none; cursor: pointer; font-size: 14px; font-weight: 500; color: #64748b; border-bottom: 2px solid transparent; }
                .tab.active { color: #667eea; border-bottom-color: #667eea; }
                .tab-content { display: none; }
                .tab-content.active { display: block; }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="header-content">
                    <h1>📊 챌린지 관리자 시스템</h1>
                    <button onclick="logout()" class="logout-btn">로그아웃</button>
                </div>
            </div>

            <div class="container">
                <!-- 통계 카드 -->
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" id="total-users">-</div>
                        <div class="stat-label">등록된 사용자</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="active-participants">-</div>
                        <div class="stat-label">활성 참여자</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="total-points">-</div>
                        <div class="stat-label">총 지급 포인트</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="completion-rate">-</div>
                        <div class="stat-label">완료율</div>
                    </div>
                </div>

                <!-- 탭 메뉴 -->
                <div class="section">
                    <div class="section-content">
                        <div class="tabs">
                            <button class="tab active" onclick="showTab('participants')">참여자 현황</button>
                            <button class="tab" onclick="showTab('user-management')">사용자 관리</button>
                            <button class="tab" onclick="showTab('detailed-progress')">상세 진행률</button>
                        </div>

                        <!-- 참여자 현황 탭 -->
                        <div id="participants" class="tab-content active">
                            <div class="section-header">
                                <div class="section-title">🎯 실시간 참여자 현황</div>
                                <div class="section-subtitle">현재 챌린지에 참여 중인 사용자들의 실시간 진행상황</div>
                            </div>
                            <div id="participants-status" class="loading">
                                데이터를 불러오는 중...
                            </div>
                        </div>

                        <!-- 사용자 관리 탭 -->
                        <div id="user-management" class="tab-content">
                            <div class="section-header">
                                <div class="section-title">👥 사용자 관리</div>
                                <div class="section-subtitle">챌린지 참여 권한이 있는 사용자를 관리합니다</div>
                            </div>
                            <div class="form-grid">
                                <div class="form-group">
                                    <label class="form-label">새 사용자 추가</label>
                                    <form action="/admin/add-user" method="post" style="display: flex; gap: 10px;">
                                        <input type="text" name="nickname" class="form-input" placeholder="사용자 닉네임" required>
                                        <button type="submit" class="btn btn-primary">추가</button>
                                    </form>
                                </div>
                                
                                <div class="form-group">
                                    <label class="form-label">CSV 파일 업로드</label>
                                    <form action="/admin/upload-csv" method="post" enctype="multipart/form-data" style="display: flex; gap: 10px;">
                                        <input type="file" name="csv_file" accept=".csv" class="form-input" required>
                                        <button type="submit" class="btn btn-primary">📁 업로드</button>
                                    </form>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">일괄 사용자 등록</label>
                                <form action="/admin/bulk-add-users" method="post">
                                    <textarea name="nicknames" class="form-textarea" placeholder="사용자 닉네임을 한 줄에 하나씩 입력하세요&#10;예:&#10;user001&#10;user002&#10;user003" required></textarea>
                                    <button type="submit" class="btn btn-primary" style="margin-top: 10px;">일괄 등록</button>
                                </form>
                            </div>

                            <div class="section-header">
                                <div class="section-title">📋 등록된 사용자 목록</div>
                            </div>
                            <div id="registered-users" class="loading">
                                사용자 목록을 불러오는 중...
                            </div>
                        </div>

                        <!-- 상세 진행률 탭 -->
                        <div id="detailed-progress" class="tab-content">
                            <div class="section-header">
                                <div class="section-title">📈 상세 진행률 분석</div>
                                <div class="section-subtitle">각 단계별 참여율과 보상 지급 현황을 확인합니다</div>
                            </div>
                            <div id="detailed-analysis" class="loading">
                                상세 분석 데이터를 불러오는 중...
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                function showTab(tabName) {
                    // 모든 탭 비활성화
                    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                    
                    // 선택된 탭 활성화
                    event.target.classList.add('active');
                    document.getElementById(tabName).classList.add('active');
                    
                    // 해당 탭의 데이터 로드
                    if (tabName === 'participants') loadParticipants();
                    else if (tabName === 'user-management') loadRegisteredUsers();
                    else if (tabName === 'detailed-progress') loadDetailedAnalysis();
                }

                function logout() {
                    document.cookie = "admin_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                    location.reload();
                }

                async function loadStats() {
                    try {
                        const [usersRes, participantsRes] = await Promise.all([
                            fetch('/admin/users'),
                            fetch('/admin/all-users')
                        ]);
                        
                        const users = await usersRes.json();
                        const participants = await participantsRes.json();
                        
                        const totalPoints = participants.reduce((sum, user) => sum + user.points, 0);
                        const completedUsers = participants.filter(user => user.progression_day >= 14).length;
                        const completionRate = participants.length > 0 ? Math.round((completedUsers / participants.length) * 100) : 0;
                        
                        document.getElementById('total-users').textContent = users.length.toLocaleString();
                        document.getElementById('active-participants').textContent = participants.length.toLocaleString();
                        document.getElementById('total-points').textContent = totalPoints.toLocaleString() + 'P';
                        document.getElementById('completion-rate').textContent = completionRate + '%';
                    } catch (error) {
                        console.error('통계 로드 실패:', error);
                    }
                }

                async function loadParticipants() {
                    try {
                        const response = await fetch('/admin/all-users');
                        const participants = await response.json();
                        const statusDiv = document.getElementById('participants-status');
                        
                        if (participants.length === 0) {
                            statusDiv.innerHTML = `
                                <div class="empty-state">
                                    <div class="empty-icon">👥</div>
                                    <div style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">아직 참여자가 없습니다</div>
                                    <div>메인 페이지에서 등록된 닉네임으로 챌린지를 시작해보세요</div>
                                </div>
                            `;
                        } else {
                            let html = `
                                <div class="table-container">
                                    <table class="table">
                                        <thead>
                                            <tr>
                                                <th>닉네임</th>
                                                <th>진행도</th>
                                                <th>포인트</th>
                                                <th>진행률</th>
                                                <th>마지막 활동</th>
                                                <th>상태</th>
                                                <th>액션</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                            `;
                            
                            participants.forEach(user => {
                                const progress = Math.round((user.progression_day / 14) * 100);
                                const lastActivity = user.last_activity === '없음' ? '없음' : new Date(user.last_activity).toLocaleString('ko-KR');
                                
                                let statusBadge = '';
                                if (user.progression_day >= 14) {
                                    statusBadge = '<span class="badge badge-success">완료</span>';
                                } else if (user.progression_day >= 8) {
                                    statusBadge = '<span class="badge badge-info">진행중</span>';
                                } else if (user.progression_day >= 1) {
                                    statusBadge = '<span class="badge badge-warning">시작함</span>';
                                } else {
                                    statusBadge = '<span class="badge badge-danger">미시작</span>';
                                }
                                
                                html += `
                                    <tr>
                                        <td><a href="/admin/user/${user.nickname}" target="_blank" class="user-link">${user.nickname}</a></td>
                                        <td><strong>DAY ${user.progression_day}</strong></td>
                                        <td><strong>${user.points.toLocaleString()}P</strong></td>
                                        <td>
                                            <div class="progress-bar">
                                                <div class="progress-fill" style="width: ${progress}%"></div>
                                            </div>
                                            <small>${progress}%</small>
                                        </td>
                                        <td><small>${lastActivity}</small></td>
                                        <td>${statusBadge}</td>
                                        <td><a href="/admin/user/${user.nickname}" target="_blank" class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px;">상세보기</a></td>
                                    </tr>
                                `;
                            });
                            
                            html += '</tbody></table></div>';
                            statusDiv.innerHTML = html;
                        }
                    } catch (error) {
                        document.getElementById('participants-status').innerHTML = `
                            <div class="empty-state">
                                <div class="empty-icon">⚠️</div>
                                <div style="color: #dc2626;">데이터를 불러오는데 실패했습니다</div>
                            </div>
                        `;
                    }
                }

                async function loadRegisteredUsers() {
                    try {
                        const response = await fetch('/admin/users');
                        const users = await response.json();
                        const usersDiv = document.getElementById('registered-users');
                        
                        if (users.length === 0) {
                            usersDiv.innerHTML = `
                                <div class="empty-state">
                                    <div class="empty-icon">📝</div>
                                    <div>등록된 사용자가 없습니다</div>
                                </div>
                            `;
                        } else {
                            let html = `
                                <div style="margin-bottom: 10px; color: #64748b;">총 ${users.length}명의 사용자가 등록되어 있습니다</div>
                                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px;">
                            `;
                            
                            users.forEach(user => {
                                html += `
                                    <div style="padding: 12px; background: #f8fafc; border-radius: 8px; border-left: 3px solid #667eea; display: flex; justify-content: space-between; align-items: center;">
                                        <span style="font-weight: 500;">${user}</span>
                                        <div style="display: flex; gap: 8px;">
                                            <form action="/admin/reset-user" method="post" style="display: inline;" onsubmit="return confirm('${user}의 진행도를 초기화하시겠습니까?')">
                                                <input type="hidden" name="nickname" value="${user}">
                                                <button type="submit" class="btn btn-secondary" style="padding: 4px 8px; font-size: 12px; background: #f59e0b; color: white;">초기화</button>
                                            </form>
                                            <form action="/admin/delete-user" method="post" style="display: inline;" onsubmit="return confirm('${user}를 완전히 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')">
                                                <input type="hidden" name="nickname" value="${user}">
                                                <button type="submit" class="btn btn-secondary" style="padding: 4px 8px; font-size: 12px; background: #dc2626; color: white;">삭제</button>
                                            </form>
                                        </div>
                                    </div>
                                `;
                            });
                            
                            html += '</div>';
                            usersDiv.innerHTML = html;
                        }
                    } catch (error) {
                        document.getElementById('registered-users').innerHTML = '<div style="color: #dc2626;">사용자 목록을 불러오는데 실패했습니다</div>';
                    }
                }

                async function loadDetailedAnalysis() {
                    try {
                        const response = await fetch('/admin/detailed-analysis');
                        const data = await response.json();
                        const analysisDiv = document.getElementById('detailed-analysis');
                        
                        let html = `
                            <div class="table-container">
                                <table class="table">
                                    <thead>
                                        <tr>
                                            <th>단계</th>
                                            <th>참여자 수</th>
                                            <th>완료율</th>
                                            <th>평균 포인트</th>
                                            <th>총 지급 포인트</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                        `;
                        
                        for (let day = 1; day <= 14; day++) {
                            const dayData = data.find(d => d.day === day) || { participants: 0, completion_rate: 0, avg_points: 0, total_points: 0 };
                            html += `
                                <tr>
                                    <td><strong>DAY ${day}</strong></td>
                                    <td>${dayData.participants}명</td>
                                    <td>${dayData.completion_rate}%</td>
                                    <td>${dayData.avg_points.toLocaleString()}P</td>
                                    <td>${dayData.total_points.toLocaleString()}P</td>
                                </tr>
                            `;
                        }
                        
                        html += '</tbody></table></div>';
                        analysisDiv.innerHTML = html;
                    } catch (error) {
                        document.getElementById('detailed-analysis').innerHTML = '<div style="color: #dc2626;">상세 분석 데이터를 불러오는데 실패했습니다</div>';
                    }
                }

                // 페이지 로드시 초기 데이터 로드
                document.addEventListener('DOMContentLoaded', function() {
                    loadStats();
                    loadParticipants();
                });

                // 5분마다 데이터 자동 새로고침
                setInterval(() => {
                    loadStats();
                    if (document.getElementById('participants').classList.contains('active')) {
                        loadParticipants();
                    }
                }, 300000);
            </script>
        </body>
        </html>
        """

    @app.post("/admin/login")
    async def admin_login(password: str = Form(...)):
        if password == ADMIN_PASSWORD:
            response = RedirectResponse(url="/admin", status_code=302)
            response.set_cookie(key="admin_session", value=ADMIN_PASSWORD, max_age=86400)  # 24시간
            return response
        else:
            raise HTTPException(status_code=401, detail="잘못된 비밀번호입니다")

    @app.get("/admin/user/{nickname}", response_class=HTMLResponse)
    async def get_user_detail_page(nickname: str, admin_session: str = Cookie(None)):
        if admin_session != ADMIN_PASSWORD:
            return RedirectResponse(url="/admin")
            
        if not db.exists(f"user:{nickname}:valid"):
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        user_data = {
            "nickname": nickname,
            "points": db.get(f"user:{nickname}:points", 0),
            "progression_day": db.get(f"user:{nickname}:progression_day", 1),
            "survey_step": db.get(f"user:{nickname}:survey_step", 0),
            "survey_responses": db.get(f"user:{nickname}:survey_responses", {}),
            "viewed_cards": db.get(f"user:{nickname}:viewed_cards", []),
            "video_progress": db.get(f"user:{nickname}:video_progress", 0),
            "payment_log": db.get(f"user:{nickname}:payment_log", {}),
            "last_activity": db.get(f"user:{nickname}:last_activity_date", "없음")
        }
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{nickname} - 사용자 상세 정보</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f8fafc; }}
                .container {{ max-width: 1000px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .back-btn {{ display: inline-block; margin-top: 10px; padding: 8px 16px; background: rgba(255,255,255,0.2); color: white; text-decoration: none; border-radius: 6px; }}
                .back-btn:hover {{ background: rgba(255,255,255,0.3); }}
                .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                .info-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
                .info-card h3 {{ margin: 0 0 15px 0; color: #667eea; font-size: 18px; }}
                .info-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #e5e7eb; }}
                .info-label {{ font-weight: 600; color: #374151; }}
                .info-value {{ color: #64748b; }}
                .badge {{ padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
                .badge-success {{ background: #d1fae5; color: #065f46; }}
                .badge-warning {{ background: #fef3c7; color: #92400e; }}
                .badge-info {{ background: #dbeafe; color: #1e40af; }}
                .progress-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
                .progress-bar {{ width: 100%; height: 20px; background: #e5e7eb; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
                .progress-fill {{ height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 10px; }}
                .activity-list {{ list-style: none; padding: 0; }}
                .activity-item {{ padding: 12px; background: #f8fafc; margin-bottom: 8px; border-radius: 8px; border-left: 4px solid #667eea; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>👤 {user_data['nickname']} 상세 정보</h1>
                    <a href="/admin" class="back-btn">← 관리자 홈으로 돌아가기</a>
                </div>
                
                <div class="progress-card">
                    <h3>🎯 전체 진행률</h3>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {(user_data['progression_day'] / 14) * 100}%"></div>
                    </div>
                    <div style="text-align: center; margin-top: 10px;">
                        <strong>DAY {user_data['progression_day']} / 14 ({round((user_data['progression_day'] / 14) * 100)}% 완료)</strong>
                    </div>
                </div>
                
                <div class="info-grid">
                    <div class="info-card">
                        <h3>📊 기본 정보</h3>
                        <div class="info-row">
                            <span class="info-label">닉네임</span>
                            <span class="info-value">{user_data['nickname']}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">총 포인트</span>
                            <span class="info-value"><strong>{user_data['points']:,}P</strong></span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">현재 단계</span>
                            <span class="info-value">DAY {user_data['progression_day']}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">마지막 활동</span>
                            <span class="info-value">{user_data['last_activity'] if user_data['last_activity'] != '없음' else '없음'}</span>
                        </div>
                    </div>
                    
                    <div class="info-card">
                        <h3>📝 설문 현황 (DAY 2)</h3>
                        <div class="info-row">
                            <span class="info-label">설문 진행도</span>
                            <span class="info-value">{user_data['survey_step']}/3 완료</span>
                        </div>
                        {''.join([f'<div class="info-row"><span class="info-label">질문 {qid.split("_")[1]}</span><span class="info-value">{resp}</span></div>' for qid, resp in user_data['survey_responses'].items()])}
                    </div>
                    
                    <div class="info-card">
                        <h3>🎴 카드뉴스 현황 (DAY 3-6)</h3>
                        <div class="info-row">
                            <span class="info-label">확인한 카드</span>
                            <span class="info-value">{len(user_data['viewed_cards'])}/4 개</span>
                        </div>
                        {(''.join([f'<div class="activity-item">DAY {card} 카드 확인 완료 ✅</div>' for card in user_data['viewed_cards']]) if user_data['viewed_cards'] else '<div class="activity-item">아직 확인한 카드가 없습니다</div>')}
                    </div>
                    
                    <div class="info-card">
                        <h3>📹 영상 시청 현황 (DAY 7)</h3>
                        <div class="info-row">
                            <span class="info-label">시청 진행도</span>
                            <span class="info-value">{user_data['video_progress']}%</span>
                        </div>
                        <div class="progress-bar" style="height: 10px;">
                            <div class="progress-fill" style="width: {user_data['video_progress']}%"></div>
                        </div>
                    </div>
                    
                    <div class="info-card">
                        <h3>💰 결제 챌린지 현황 (DAY 8-14)</h3>
                        <div class="info-row">
                            <span class="info-label">참여 횟수</span>
                            <span class="info-value">{len(user_data['payment_log'])}/7 회</span>
                        </div>
                        {(''.join([f'<div class="activity-item">DAY {day.split("_")[1]}: {amount:,}원 입금 💳</div>' for day, amount in user_data['payment_log'].items()]) if user_data['payment_log'] else '<div class="activity-item">아직 결제 활동이 없습니다</div>')}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    @app.post("/admin/add-user")
    async def add_user(nickname: str = Form(...), admin_session: str = Cookie(None)):
        if admin_session != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="권한이 없습니다")
        
        allowed_users = db.get("allowed_users", [])
        if nickname not in allowed_users:
            allowed_users.append(nickname)
            db.set("allowed_users", allowed_users)
        return RedirectResponse(url="/admin", status_code=302)
    
    @app.post("/admin/bulk-add-users")
    async def bulk_add_users(nicknames: str = Form(...), admin_session: str = Cookie(None)):
        if admin_session != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="권한이 없습니다")
            
        nickname_list = [nick.strip() for nick in nicknames.split('\n') if nick.strip()]
        allowed_users = db.get("allowed_users", [])
        
        added_count = 0
        for nickname in nickname_list:
            if nickname not in allowed_users:
                allowed_users.append(nickname)
                added_count += 1
        
        db.set("allowed_users", allowed_users)
        return RedirectResponse(url="/admin", status_code=302)
    
    @app.post("/admin/upload-csv")
    async def upload_csv(csv_file: UploadFile = File(...), admin_session: str = Cookie(None)):
        if admin_session != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="권한이 없습니다")
            
        if not csv_file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="CSV 파일만 업로드 가능합니다.")
        
        content = await csv_file.read()
        csv_reader = csv.reader(io.StringIO(content.decode('utf-8')))
        
        allowed_users = db.get("allowed_users", [])
        added_count = 0
        
        next(csv_reader, None)
        
        for row in csv_reader:
            if row and row[0].strip():
                nickname = row[0].strip()
                if nickname not in allowed_users:
                    allowed_users.append(nickname)
                    added_count += 1
        
        db.set("allowed_users", allowed_users)
        return RedirectResponse(url="/admin", status_code=302)
    
    @app.get("/admin/users")
    async def get_users(admin_session: str = Cookie(None)):
        if admin_session != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="권한이 없습니다")
        return db.get("allowed_users", [])

    @app.post("/admin/delete-user")
    async def delete_user(nickname: str = Form(...), admin_session: str = Cookie(None)):
        if admin_session != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="권한이 없습니다")
        
        allowed_users = db.get("allowed_users", [])
        if nickname in allowed_users:
            allowed_users.remove(nickname)
            db.set("allowed_users", allowed_users)
            
            # 사용자 데이터도 함께 삭제
            user_keys = [
                f"user:{nickname}:valid",
                f"user:{nickname}:points",
                f"user:{nickname}:progression_day",
                f"user:{nickname}:survey_step",
                f"user:{nickname}:survey_responses",
                f"user:{nickname}:viewed_cards",
                f"user:{nickname}:video_progress",
                f"user:{nickname}:payment_log",
                f"user:{nickname}:last_activity_date"
            ]
            
            for key in user_keys:
                db.delete(key)
        
        return RedirectResponse(url="/admin", status_code=302)

    @app.post("/admin/reset-user")
    async def reset_user(nickname: str = Form(...), admin_session: str = Cookie(None)):
        if admin_session != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="권한이 없습니다")
        
        if nickname in db.get("allowed_users", []):
            # 사용자 진행도 초기화
            db.set(f"user:{nickname}:points", 5000)
            db.set(f"user:{nickname}:progression_day", 1)
            db.set(f"user:{nickname}:survey_step", 0)
            db.set(f"user:{nickname}:survey_responses", {})
            db.set(f"user:{nickname}:viewed_cards", [])
            db.set(f"user:{nickname}:video_progress", 0)
            db.set(f"user:{nickname}:payment_log", {})
            db.delete(f"user:{nickname}:last_activity_date")
        
        return RedirectResponse(url="/admin", status_code=302)

    @app.get("/admin/detailed-analysis")
    async def get_detailed_analysis(admin_session: str = Cookie(None)):
        if admin_session != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="권한이 없습니다")
        
        allowed_users = db.get("allowed_users", [])
        analysis_data = []
        
        for day in range(1, 15):
            participants = []
            total_points = 0
            
            for nickname in allowed_users:
                if db.exists(f"user:{nickname}:valid"):
                    user_day = db.get(f"user:{nickname}:progression_day", 1)
                    if user_day >= day:
                        participants.append(nickname)
                        user_points = db.get(f"user:{nickname}:points", 0)
                        total_points += user_points
            
            participant_count = len(participants)
            total_users = len([u for u in allowed_users if db.exists(f"user:{u}:valid")])
            completion_rate = round((participant_count / total_users * 100) if total_users > 0 else 0)
            avg_points = round(total_points / participant_count) if participant_count > 0 else 0
            
            analysis_data.append({
                "day": day,
                "participants": participant_count,
                "completion_rate": completion_rate,
                "avg_points": avg_points,
                "total_points": total_points
            })
        
        return analysis_data

