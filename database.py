# database.py
import json
import os
from threading import Lock

DB_FILE = "db.json"
_db = {}
_lock = Lock()

def load_db():
    global _db
    with _lock:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                _db = json.load(f)
        else:
            print(f"경고: '{DB_FILE}' 파일이 없습니다. setup_db.py를 먼저 실행해주세요.")
            _db = {}

def save_db():
    with _lock:
        with open(DB_FILE, "w") as f:
            json.dump(_db, f, indent=4)

def get(key, default=None):
    return _db.get(key, default)

def set(key, value):
    _db[key] = value
    save_db()

def exists(key):
    return key in _db

def delete(key):
    if key in _db:
        del _db[key]
        save_db()
        return True
    return Falsef exists(key):
    return key in _db