import hashlib
import sqlite3
from functools import wraps
from flask import session, redirect, request, abort
from config import DATABASE


def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()


def verify_login(username, pin):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT id, username, role, pin_hash FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    if row and row["pin_hash"] == hash_pin(pin):
        return {"id": row["id"], "username": row["username"], "role": row["role"]}
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(f"/giris?next={request.path}")
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect(f"/giris?next={request.path}")
            if session.get("role") not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator
