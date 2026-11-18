"""Request correlation, rate limiting, security headers, and durable audit logging."""
import json,sqlite3,time,uuid
from collections import defaultdict,deque
from pathlib import Path
from threading import Lock
from flask import g,request
from backend.errors import ApiError

class ProductionControls:
    def __init__(self,db_path="data/audit.db",requests_per_minute=120,mutations_per_minute=30):
        self.path=Path(db_path);self.path.parent.mkdir(parents=True,exist_ok=True);self.limit=requests_per_minute;self.mutation_limit=mutations_per_minute;self.windows=defaultdict(deque);self.lock=Lock()
        with self._connect() as db:db.execute("CREATE TABLE IF NOT EXISTS audit_log(id TEXT PRIMARY KEY,request_id TEXT NOT NULL,method TEXT NOT NULL,path TEXT NOT NULL,actor TEXT,ip TEXT,status INTEGER,duration_ms REAL,created_at TEXT NOT NULL,metadata TEXT NOT NULL)")
    def _connect(self):return sqlite3.connect(self.path)
    def before(self):
        supplied=request.headers.get("X-Request-ID","");g.request_id=supplied[:64] if supplied and all(char.isalnum() or char in "-_" for char in supplied) else str(uuid.uuid4());g.started=time.monotonic();key=f"{request.remote_addr}:{request.method!='GET'}";limit=self.mutation_limit if request.method!="GET" else self.limit;now=time.time()
        with self.lock:
            window=self.windows[key]
            while window and window[0]<now-60:window.popleft()
            if len(window)>=limit:raise ApiError("Request rate limit exceeded. Retry later.",429,"rate_limited")
            window.append(now)
    def after(self,response):
        response.headers["X-Request-ID"]=g.get("request_id","");response.headers["X-Content-Type-Options"]="nosniff";response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
        if request.method!="OPTIONS":
            duration=(time.monotonic()-g.get("started",time.monotonic()))*1000;actor=request.headers.get("X-Nexora-Dev-User") if request.method!="GET" else None
            try:
                with self._connect() as db:db.execute("INSERT INTO audit_log VALUES(?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),g.get("request_id",""),request.method,request.path,actor,request.remote_addr,response.status_code,duration,time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),json.dumps({"content_length":request.content_length,"user_agent":request.user_agent.string[:200]})))
            except sqlite3.Error:pass
        return response
    def register(self,app):app.before_request(self.before);app.after_request(self.after)
