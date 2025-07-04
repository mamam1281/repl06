
from fastapi import HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import database_json as db
from datetime import datetime

def setup_admin_routes(app, database):
    # 세션 미들웨어 추가
    app.add_middleware(SessionMiddleware, secret_key="admin-secret-key-6969")
    
    def check_admin_auth(request: Request):
        if not request.session.get("admin_authenticated"):
            raise HTTPException(status_code=401, detail="관리자 인증이 필요합니다.")
    
    @app.get("/admin", response_class=HTMLResponse)
    async def admin_login_page(request: Request):
        if request.session.get("admin_authenticated"):
            return RedirectResponse(url="/admin/dashboard")
        
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>관리자 로그인</title>
            <style>
                body { font-family: Arial, sans-serif; background: #1f2937; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
                .login-container { background: #374151; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .form-group { margin-bottom: 1rem; }
                label { display: block; margin-bottom: 0.5rem; color: #e5e7eb; }
                input { width: 200px; padding: 8px; border: 1px solid #6b7280; border-radius: 4px; background: #1f2937; color: white; }
                button { background: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #2563eb; }
                .error { color: #ef4444; margin-top: 0.5rem; }
            </style>
        </head>
        <body>
            <div class="login-container">
                <h2>관리자 로그인</h2>
                <form method="post" action="/admin/login">
                    <div class="form-group">
                        <label>비밀번호:</label>
                        <input type="password" name="password" required>
                    </div>
                    <button type="submit">로그인</button>
                </form>
            </div>
        </body>
        </html>
        """)
    
    @app.post("/admin/login")
    async def admin_login(request: Request, password: str = Form(...)):
        if password == "6969":
            request.session["admin_authenticated"] = True
            return RedirectResponse(url="/admin/dashboard", status_code=302)
        else:
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>로그인 실패</title>
                <style>
                    body { font-family: Arial, sans-serif; background: #1f2937; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
                    .error-container { background: #374151; padding: 2rem; border-radius: 8px; text-align: center; }
                    .error { color: #ef4444; margin-bottom: 1rem; }
                    a { color: #60a5fa; text-decoration: none; }
                </style>
            </head>
            <body>
                <div class="error-container">
                    <div class="error">비밀번호가 올바르지 않습니다.</div>
                    <a href="/admin">다시 시도하기</a>
                </div>
            </body>
            </html>
            """)
    
    @app.get("/admin/logout")
    async def admin_logout(request: Request):
        request.session.clear()
        return RedirectResponse(url="/admin")
    
    @app.get("/admin/dashboard", response_class=HTMLResponse)
    async def admin_dashboard(request: Request):
        check_admin_auth(request)
        
        # 전체 통계 조회
        global_stats = db.get("global_stats", {})
        all_users = db.get_all_users()
        
        # 사용자별 상세 정보 조회
        user_details = []
        for nickname in all_users:
            user_info = {
                "nickname": nickname,
                "points": db.get(f"user:{nickname}:points", 0),
                "progression_day": db.get(f"user:{nickname}:progression_day", 1),
                "survey_step": db.get(f"user:{nickname}:survey_step", 0),
                "viewed_cards": len(db.get(f"user:{nickname}:viewed_cards", [])),
                "video_progress": db.get(f"user:{nickname}:video_progress", 0),
                "payment_activities": len(db.get(f"user:{nickname}:payment_activities", [])),
                "created_at": db.get(f"user:{nickname}:created_at", "알 수 없음"),
                "last_activity": db.get(f"user:{nickname}:last_activity_date", "없음")
            }
            user_details.append(user_info)
        
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>관리자 대시보드 (JSON 버전)</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #1f2937; color: white; margin: 0; padding: 20px; }}
                .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }}
                .header h1 {{ color: #60a5fa; }}
                .logout-btn {{ background: #ef4444; color: white; padding: 8px 16px; border: none; border-radius: 4px; text-decoration: none; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
                .stat-card {{ background: #374151; padding: 1rem; border-radius: 8px; text-align: center; }}
                .stat-number {{ font-size: 2rem; font-weight: bold; color: #60a5fa; }}
                .user-table {{ width: 100%; background: #374151; border-radius: 8px; overflow: hidden; }}
                .user-table th, .user-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #4b5563; }}
                .user-table th {{ background: #4b5563; color: #e5e7eb; }}
                .user-table tr:hover {{ background: #4b5563; }}
                .action-btn {{ background: #3b82f6; color: white; padding: 4px 8px; border: none; border-radius: 4px; margin-right: 4px; cursor: pointer; font-size: 12px; }}
                .delete-btn {{ background: #ef4444; }}
                .add-user-form {{ background: #374151; padding: 1rem; border-radius: 8px; margin-bottom: 2rem; }}
                .form-group {{ margin-bottom: 1rem; }}
                .form-group input {{ padding: 8px; border: 1px solid #6b7280; border-radius: 4px; background: #1f2937; color: white; }}
                .form-group button {{ background: #10b981; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>관리자 대시보드 (JSON 버전)</h1>
                <a href="/admin/logout" class="logout-btn">로그아웃</a>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{global_stats.get('participants', 0)}</div>
                    <div>총 참여자</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{global_stats.get('total_points_awarded', 0):,}</div>
                    <div>총 지급 포인트</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{global_stats.get('video_viewers', 0)}</div>
                    <div>영상 완주자</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{global_stats.get('card_finishers', 0)}</div>
                    <div>카드 완주자</div>
                </div>
            </div>
            
            <div class="add-user-form">
                <h3>사용자 추가</h3>
                <form method="post" action="/admin/add-user">
                    <div class="form-group">
                        <input type="text" name="nickname" placeholder="닉네임 입력" required>
                        <button type="submit">추가</button>
                    </div>
                </form>
            </div>
            
            <table class="user-table">
                <thead>
                    <tr>
                        <th>닉네임</th>
                        <th>포인트</th>
                        <th>진행일</th>
                        <th>설문단계</th>
                        <th>카드확인</th>
                        <th>영상진행률</th>
                        <th>결제활동</th>
                        <th>가입일</th>
                        <th>최종활동</th>
                        <th>액션</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join([f'''
                    <tr>
                        <td>{user["nickname"]}</td>
                        <td>{user["points"]:,}</td>
                        <td>{user["progression_day"]}일차</td>
                        <td>{user["survey_step"]}/3</td>
                        <td>{user["viewed_cards"]}/4</td>
                        <td>{user["video_progress"]:.1f}%</td>
                        <td>{user["payment_activities"]}회</td>
                        <td>{user["created_at"][:10] if user["created_at"] != "알 수 없음" else "알 수 없음"}</td>
                        <td>{user["last_activity"][:10] if user["last_activity"] != "없음" else "없음"}</td>
                        <td>
                            <button class="action-btn" onclick="editUser('{user["nickname"]}')">편집</button>
                            <button class="action-btn delete-btn" onclick="deleteUser('{user["nickname"]}')">삭제</button>
                        </td>
                    </tr>
                    ''' for user in user_details])}
                </tbody>
            </table>
            
            <script>
                function editUser(nickname) {{
                    const newPoints = prompt(`${{nickname}}의 새로운 포인트를 입력하세요:`);
                    if (newPoints !== null) {{
                        fetch('/admin/edit-user', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                            body: `nickname=${{nickname}}&points=${{newPoints}}`
                        }}).then(() => location.reload());
                    }}
                }}
                
                function deleteUser(nickname) {{
                    if (confirm(`${{nickname}} 사용자를 정말 삭제하시겠습니까?`)) {{
                        fetch('/admin/delete-user', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                            body: `nickname=${{nickname}}`
                        }}).then(() => location.reload());
                    }}
                }}
            </script>
        </body>
        </html>
        """)
    
    @app.post("/admin/add-user")
    async def add_user(request: Request, nickname: str = Form(...)):
        check_admin_auth(request)
        
        allowed_users = db.get("allowed_users", [])
        if nickname not in allowed_users:
            allowed_users.append(nickname)
            db.set("allowed_users", allowed_users)
        
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    
    @app.post("/admin/edit-user")
    async def edit_user(request: Request, nickname: str = Form(...), points: int = Form(...)):
        check_admin_auth(request)
        
        if db.exists(f"user:{nickname}:valid"):
            db.set(f"user:{nickname}:points", points)
        
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    
    @app.post("/admin/delete-user")
    async def delete_user(request: Request, nickname: str = Form(...)):
        check_admin_auth(request)
        
        # 사용자 데이터 삭제
        user_keys = [
            f"user:{nickname}:valid",
            f"user:{nickname}:points",
            f"user:{nickname}:progression_day",
            f"user:{nickname}:survey_step",
            f"user:{nickname}:viewed_cards",
            f"user:{nickname}:video_progress",
            f"user:{nickname}:payment_activities",
            f"user:{nickname}:created_at",
            f"user:{nickname}:last_activity_date",
            f"user:{nickname}:survey_responses"
        ]
        
        for key in user_keys:
            db.delete(key)
        
        return RedirectResponse(url="/admin/dashboard", status_code=302)
