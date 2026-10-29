"""Disposable fresh-database auth proof across real API and PostgreSQL restarts.

Opt in only with UI_AUTH_TEST_DATABASE_URL naming learntrack_ui_auth_test on loopback.
No production fallback, AI requests, persisted tokens or real credentials.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[2]
url = make_url(os.environ.get("UI_AUTH_TEST_DATABASE_URL", ""))
if url.get_backend_name() != "postgresql" or url.host not in ("127.0.0.1", "localhost") or url.database not in ("learntrack_ui_auth_test", "learntrack_ui_auth_test_retry"):
    raise RuntimeError("Requires an explicitly disposable loopback learntrack_ui_auth_test database")
value = url.render_as_string(hide_password=False)
env = {**os.environ, "DATABASE_URL":value, "ALEMBIC_DATABASE_URL":value, "PYTHON_DOTENV_DISABLED":"1", "SECRET_KEY":"synthetic-ui-auth-restart-key-at-least-32-characters", "GEMINI_API_KEY":"synthetic-disabled", "AI_ENABLED":"false", "REGISTRATION_ENABLED":"true", "FRONTEND_ORIGINS":"http://127.0.0.1:3100"}
state_path = ROOT / ".ui-auth-restart.json"
engine = create_engine(url)
mode = sys.argv[1]
if mode == "seed":
    # The database must actually be empty before the normal migration path runs.
    from sqlalchemy import inspect
    assert not inspect(engine).get_table_names()
    subprocess.run([sys.executable,"scripts/migrate_local.py"],cwd=ROOT/"backend",env=env,check=True)
    subprocess.run([sys.executable,"scripts/check_local.py","--database"],cwd=ROOT/"backend",env=env,check=True)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM users")).scalar_one() == 0
        assert connection.execute(text("SELECT count(*) FROM learning_tracks")).scalar_one() == 0
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "f40100000001"


def call(path, data=None, token=None):
    headers = {"Content-Type":"application/json"}
    if token: headers["Authorization"] = "Bearer " + token
    body = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request("http://127.0.0.1:8117"+path, data=body, headers=headers)
    try:
        with urllib.request.urlopen(request,timeout=10) as response: return response.status,json.load(response)
    except urllib.error.HTTPError as error: return error.code,json.load(error)


def login(email):
    code,result = call("/login", {"email":email,"password":"synthetic-auth-proof-only"})
    assert code == 200
    return result["access_token"]


proc = subprocess.Popen([sys.executable,"-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8117"],cwd=ROOT/"backend",env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
try:
    for _ in range(100):
        try:
            if call("/health")[0] == 200: break
        except OSError: pass
        if proc.poll() is not None: raise RuntimeError("Synthetic API failed to start")
        time.sleep(.1)
    else: raise RuntimeError("Synthetic API readiness timed out")
    own = {"username":"restart-learner","email":"restart-learner@example.com","password":"synthetic-auth-proof-only"}
    other = {**own,"username":"other-learner","email":"other-learner@example.com"}
    if mode == "seed":
        code,user = call("/register",own); assert code == 200
        code,other_user = call("/register",other); assert code == 200
        token = login(own["email"])
        assert call("/me",token=token)[1]["id"] == user["id"]
        code,track = call("/learning-tracks",{"name":"Restart-proof synthetic path"},token); assert code == 201
        assert call("/register",own)[0] == 400
        assert call("/users/"+str(other_user["id"]),token=token)[0] == 404
        state_path.write_text(json.dumps({"user_id":user["id"],"other_user_id":other_user["id"],"track_id":track["id"]}),encoding="utf-8")
        print("Fresh migrations, pgvector, signup/login/me, track creation and owner checks passed. API stopped; restart disposable PostgreSQL before verify.")
    elif mode == "verify":
        state = json.loads(state_path.read_text(encoding="utf-8"))
        token = login(own["email"])
        assert call("/me",token=token)[1]["id"] == state["user_id"]
        tracks = call("/learning-tracks",token=token)[1]
        assert len(tracks) == 1 and tracks[0]["id"] == state["track_id"]
        assert call("/register",own)[0] == 400
        other_token = login(other["email"])
        assert call("/learning-tracks",token=other_token)[1] == []
        assert call("/users/"+str(state["user_id"]),token=other_token)[0] == 404
        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM users")).scalar_one() == 2
            assert connection.execute(text("SELECT count(*) FROM learning_tracks")).scalar_one() == 1
        output = ROOT / "test-artifacts/ui-auth/database-readiness.json"
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps({"status":"PASS","initial_database_empty":True,"alembic_head":"f40100000001","pgvector":True,"accounts_after_restart":2,"tracks_after_restart":1,"api_process_restarted":True,"postgresql_restarted":True,"password_hash_compatible":True,"duplicate_retry_rejected":True,"owner_isolation":True,"live_ai":False},indent=2)+"\n",encoding="utf-8")
        state_path.unlink()
        print("Account and path persisted across PostgreSQL and API restart. Duplicate retry and other-owner privacy passed.")
    else: raise RuntimeError("Use seed or verify")
finally:
    proc.terminate(); proc.wait(timeout=20); engine.dispose()
