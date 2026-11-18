"""In-process metrics, structured error tracking, freshness, and alert evaluation."""
import json,logging,sqlite3,time,uuid
from collections import defaultdict,deque
from datetime import datetime,timezone
from pathlib import Path

class JsonFormatter(logging.Formatter):
    def format(self,record):
        payload={"timestamp":datetime.now(timezone.utc).isoformat(),"level":record.levelname,"logger":record.name,"message":record.getMessage()}
        for key in ("request_id","method","path","status","duration_ms","provider","metric"): 
            if hasattr(record,key):payload[key]=getattr(record,key)
        if record.exc_info:payload["exception"]=self.formatException(record.exc_info)
        return json.dumps(payload,default=str)

class ObservabilityService:
    def __init__(self,db_path="data/observability.db"):
        self.path=Path(db_path);self.path.parent.mkdir(parents=True,exist_ok=True);self.counters=defaultdict(int);self.latencies=defaultdict(lambda:deque(maxlen=2000));self.freshness={};self.started=time.time()
        with self._connect() as db:db.executescript("CREATE TABLE IF NOT EXISTS errors(id TEXT PRIMARY KEY,request_id TEXT,error_type TEXT,message TEXT,path TEXT,created_at TEXT);CREATE TABLE IF NOT EXISTS alerts(id TEXT PRIMARY KEY,severity TEXT,metric TEXT,message TEXT,created_at TEXT,resolved INTEGER DEFAULT 0);")
        handler=logging.StreamHandler();handler.setFormatter(JsonFormatter());root=logging.getLogger();root.handlers=[handler];root.setLevel(logging.INFO)
    def _connect(self):db=sqlite3.connect(self.path);db.row_factory=sqlite3.Row;return db
    def observe(self,name,value_ms):self.latencies[name].append(float(value_ms))
    def increment(self,name,amount=1):self.counters[name]+=amount
    def mark_freshness(self,component,when=None,metadata=None):self.freshness[component]={"timestamp":when or datetime.now(timezone.utc).isoformat(),"metadata":metadata or {}}
    def error(self,error,request_id=None,path=None):
        with self._connect() as db:db.execute("INSERT INTO errors VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),request_id,type(error).__name__,str(error)[:1000],path,datetime.now(timezone.utc).isoformat()))
        self.increment("errors")
    def evaluate_alerts(self):
        alerts=[];total=self.counters["api_total"];rate=self.counters["api_errors"]/total if total else 0
        if total>=20 and rate>.05:alerts.append(("high","api_success_rate",f"API error rate is {rate:.1%}."))
        for component,item in self.freshness.items():
            try:
                parsed=datetime.fromisoformat(item["timestamp"].replace("Z","+00:00"));parsed=parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed;age=(datetime.now(timezone.utc)-parsed).total_seconds()
            except Exception:continue
            if age>86400:alerts.append(("medium",f"{component}_freshness",f"{component} data is {age/3600:.1f} hours old."))
        with self._connect() as db:
            existing={(row["metric"],row["message"]) for row in db.execute("SELECT metric,message FROM alerts WHERE resolved=0")}
            for severity,metric,message in alerts:
                if (metric,message) not in existing:db.execute("INSERT INTO alerts VALUES(?,?,?,?,?,0)",(str(uuid.uuid4()),severity,metric,message,datetime.now(timezone.utc).isoformat()))
            return [dict(row) for row in db.execute("SELECT * FROM alerts WHERE resolved=0 ORDER BY created_at DESC")]
    def status(self,pipeline=None,model=None):
        def summary(values):
            ordered=sorted(values);return {"count":len(ordered),"average_ms":round(sum(ordered)/len(ordered),2) if ordered else None,"p95_ms":round(ordered[min(len(ordered)-1,int(len(ordered)*.95))],2) if ordered else None}
        total=self.counters["api_total"];cache_total=self.counters["cache_hit"]+self.counters["cache_miss"]
        pipeline_status=pipeline.dashboard() if pipeline else {"jobs":[],"unresolved_dead_letters":0}
        coverage=None
        try:
            model._load();coverage={"scored":len(model._scores),"universe":model._manifest.get("constituent_count",len(model._scores)),"model_version":model._manifest.get("model_version"),"data_through":model._manifest.get("data_through")}
        except Exception:pass
        return {"status":"degraded" if self.counters["api_errors"] and total and self.counters["api_errors"]/total>.05 else "operational","uptime_seconds":int(time.time()-self.started),"api":{"requests":total,"success_rate":round((total-self.counters["api_errors"])/total,4) if total else 1,"latency":summary(self.latencies["request"])},"providers":{name.split(":",1)[1]:summary(values) for name,values in self.latencies.items() if name.startswith("provider:")},"cache":{"hit_rate":round(self.counters["cache_hit"]/cache_total,4) if cache_total else None,"hits":self.counters["cache_hit"],"misses":self.counters["cache_miss"],"stale_served":self.counters["cache_stale"]},"model":{"inference_latency":summary(self.latencies["model_inference"]),"coverage":coverage},"freshness":self.freshness,"background_jobs":{"latest":pipeline_status.get("jobs",[]),"dead_letters":pipeline_status.get("unresolved_dead_letters",0)},"alerts":self.evaluate_alerts()}
