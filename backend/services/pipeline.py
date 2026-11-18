"""Observable data-pipeline job orchestration with retries and dead letters."""
import json,random,sqlite3,time,traceback,uuid
from datetime import datetime,timezone
from pathlib import Path

class PipelineOrchestrator:
    def __init__(self,db_path="data/pipeline.db"):
        self.path=Path(db_path);self.path.parent.mkdir(parents=True,exist_ok=True);self.handlers={}
        with self._connect() as db:db.executescript("CREATE TABLE IF NOT EXISTS job_runs(id TEXT PRIMARY KEY,job_name TEXT NOT NULL,status TEXT NOT NULL,started_at TEXT NOT NULL,finished_at TEXT,rows_processed INTEGER DEFAULT 0,provider_failures INTEGER DEFAULT 0,retry_count INTEGER DEFAULT 0,freshness_at TEXT,error TEXT,metadata TEXT NOT NULL);CREATE TABLE IF NOT EXISTS dead_letters(id TEXT PRIMARY KEY,job_name TEXT,payload TEXT,error TEXT,created_at TEXT NOT NULL,resolved INTEGER DEFAULT 0);")
    def _connect(self):db=sqlite3.connect(self.path);db.row_factory=sqlite3.Row;return db
    def register(self,name,handler):self.handlers[name]=handler
    def run(self,name,payload=None,max_retries=3):
        if name not in self.handlers:raise ValueError(f"Unknown pipeline job: {name}")
        run_id=str(uuid.uuid4());started=datetime.now(timezone.utc).isoformat()
        with self._connect() as db:db.execute("INSERT INTO job_runs(id,job_name,status,started_at,metadata) VALUES(?,?,?,?,?)",(run_id,name,"running",started,json.dumps(payload or {})))
        failures=0
        for attempt in range(max_retries+1):
            try:
                result=self.handlers[name](payload or {}) or {};finished=datetime.now(timezone.utc).isoformat()
                with self._connect() as db:db.execute("UPDATE job_runs SET status='succeeded',finished_at=?,rows_processed=?,provider_failures=?,retry_count=?,freshness_at=?,metadata=? WHERE id=?",(finished,int(result.get("rows_processed",0)),failures,attempt,result.get("freshness_at",finished),json.dumps(result),run_id))
                return self.get(run_id)
            except Exception as error:
                failures+=1
                if attempt<max_retries:time.sleep(min(.25*(2**attempt)+random.random()*.1,2));continue
                finished=datetime.now(timezone.utc).isoformat();message=f"{type(error).__name__}: {error}"
                with self._connect() as db:db.execute("UPDATE job_runs SET status='failed',finished_at=?,provider_failures=?,retry_count=?,error=? WHERE id=?",(finished,failures,attempt,message,run_id));db.execute("INSERT INTO dead_letters VALUES(?,?,?,?,?,0)",(str(uuid.uuid4()),name,json.dumps(payload or {}),message,finished))
                return self.get(run_id)
    def get(self,run_id):
        with self._connect() as db:return dict(db.execute("SELECT * FROM job_runs WHERE id=?",(run_id,)).fetchone())
    def dashboard(self):
        with self._connect() as db:
            latest=[dict(row) for row in db.execute("SELECT * FROM job_runs WHERE id IN (SELECT id FROM (SELECT id,ROW_NUMBER() OVER(PARTITION BY job_name ORDER BY started_at DESC) rank FROM job_runs) WHERE rank=1) ORDER BY job_name")];recent=[dict(row) for row in db.execute("SELECT * FROM job_runs ORDER BY started_at DESC LIMIT 50")];dead=db.execute("SELECT COUNT(*) FROM dead_letters WHERE resolved=0").fetchone()[0]
        return {"jobs":latest,"recent_runs":recent,"unresolved_dead_letters":dead,"registered_jobs":sorted(self.handlers)}
