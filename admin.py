
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
import database as db

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
    
    @app.get("/admin/users")
    async def get_users():
        return db.get("allowed_users", [])
