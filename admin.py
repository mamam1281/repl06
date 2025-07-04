
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
            
            <script>
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
