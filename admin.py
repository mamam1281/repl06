
from fastapi import FastAPI, HTTPException, Form, File, UploadFile
from fastapi.responses import HTMLResponse
import database as db
import csv
import io

def setup_admin_routes(app):
    @app.get("/admin", response_class=HTMLResponse)
    async def admin_page():
        return """
        <!DOCTYPE html>
        <html>
        <head><title>사용자 관리</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h1>사용자 관리 시스템</h1>
            
            <h2>새 사용자 추가</h2>
            <form action="/admin/add-user" method="post">
                <input type="text" name="nickname" placeholder="사용자 닉네임" required>
                <button type="submit">추가</button>
            </form>
            
            <h2>일괄 사용자 등록</h2>
            <form action="/admin/bulk-add-users" method="post">
                <textarea name="nicknames" rows="10" cols="50" placeholder="사용자 닉네임을 한 줄에 하나씩 입력하세요&#10;예:&#10;user001&#10;user002&#10;user003" required></textarea><br>
                <button type="submit">일괄 등록</button>
            </form>
            
            <h2>CSV 파일로 일괄 등록</h2>
            <form action="/admin/upload-csv" method="post" enctype="multipart/form-data">
                <input type="file" name="csv_file" accept=".csv" required>
                <button type="submit">CSV 업로드</button>
            </form>
            <p style="font-size: 0.9em; color: #666;">CSV 파일의 첫 번째 열에 닉네임을 입력하세요. 헤더는 자동으로 건너뜁니다.</p>
            
            <h2>현재 등록된 사용자</h2>
            <ul id="user-list"></ul>
            
            <h2>챌린지 참여자 현황</h2>
            <div id="participants-status">
                <p>로딩 중...</p>
            </div>
            
            <script>
                // 등록된 사용자 목록
                fetch('/admin/users')
                    .then(r => r.json())
                    .then(users => {
                        const list = document.getElementById('user-list');
                        users.forEach(user => {
                            const li = document.createElement('li');
                            li.textContent = user;
                            list.appendChild(li);
                        });
                    });
                
                // 참여자 현황
                fetch('/admin/all-users')
                    .then(r => r.json())
                    .then(participants => {
                        const statusDiv = document.getElementById('participants-status');
                        if (participants.length === 0) {
                            statusDiv.innerHTML = '<p style="color: #999;">아직 챌린지에 참여한 사용자가 없습니다.</p><p>메인 페이지에서 등록된 닉네임으로 참여를 시작해보세요.</p>';
                        } else {
                            let html = `<p><strong>총 ${participants.length}명이 참여 중입니다.</strong></p><table border="1" style="width: 100%; border-collapse: collapse; margin-top: 10px;">`;
                            html += '<tr><th>닉네임</th><th>진행도</th><th>포인트</th><th>마지막 활동</th></tr>';
                            participants.forEach(user => {
                                const lastActivity = user.last_activity === '없음' ? '없음' : new Date(user.last_activity).toLocaleString('ko-KR');
                                html += `<tr>
                                    <td><a href="/admin/user/${user.nickname}" target="_blank">${user.nickname}</a></td>
                                    <td>DAY ${user.progression_day}</td>
                                    <td>${user.points.toLocaleString()}P</td>
                                    <td>${lastActivity}</td>
                                </tr>`;
                            });
                            html += '</table>';
                            statusDiv.innerHTML = html;
                        }
                    })
                    .catch(err => {
                        document.getElementById('participants-status').innerHTML = '<p style="color: red;">데이터를 불러오는데 실패했습니다.</p>';
                    });
            </script>
        </body>
        </html>
        """
    
    @app.post("/admin/add-user")
    async def add_user(nickname: str = Form(...)):
        allowed_users = db.get("allowed_users", [])
        if nickname not in allowed_users:
            allowed_users.append(nickname)
            db.set("allowed_users", allowed_users)
        return {"message": f"사용자 {nickname} 추가됨"}
    
    @app.post("/admin/bulk-add-users")
    async def bulk_add_users(nicknames: str = Form(...)):
        nickname_list = [nick.strip() for nick in nicknames.split('\n') if nick.strip()]
        allowed_users = db.get("allowed_users", [])
        
        added_count = 0
        for nickname in nickname_list:
            if nickname not in allowed_users:
                allowed_users.append(nickname)
                added_count += 1
        
        db.set("allowed_users", allowed_users)
        return {"message": f"{added_count}명의 사용자가 추가되었습니다. (총 {len(allowed_users)}명)"}
    
    @app.post("/admin/upload-csv")
    async def upload_csv(csv_file: UploadFile = File(...)):
        if not csv_file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="CSV 파일만 업로드 가능합니다.")
        
        content = await csv_file.read()
        csv_reader = csv.reader(io.StringIO(content.decode('utf-8')))
        
        allowed_users = db.get("allowed_users", [])
        added_count = 0
        
        # 첫 번째 행은 헤더로 간주하고 건너뜀
        next(csv_reader, None)
        
        for row in csv_reader:
            if row and row[0].strip():  # 첫 번째 열이 비어있지 않은 경우
                nickname = row[0].strip()
                if nickname not in allowed_users:
                    allowed_users.append(nickname)
                    added_count += 1
        
        db.set("allowed_users", allowed_users)
        return {"message": f"CSV에서 {added_count}명의 사용자가 추가되었습니다. (총 {len(allowed_users)}명)"}
    
    @app.get("/admin/users")
    async def get_users():
        return db.get("allowed_users", [])
