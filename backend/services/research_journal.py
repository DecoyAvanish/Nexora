"""Authenticated investment decision journal and behavioral analytics."""
import sqlite3,uuid
from datetime import datetime,timezone
from pathlib import Path
from backend.errors import ApiError
from backend.services.market_data import normalize_symbol

class ResearchJournalService:
    def __init__(self,db_path="data/research_journal.db",score_provider=None):
        self.path=Path(db_path);self.path.parent.mkdir(parents=True,exist_ok=True);self.score_provider=score_provider
        with self._connect() as db:db.executescript("""CREATE TABLE IF NOT EXISTS journal_entries(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,symbol TEXT NOT NULL,thesis_type TEXT NOT NULL,thesis TEXT NOT NULL,catalyst TEXT,entry_reasoning TEXT,risk_conditions TEXT,target_price REAL,invalidation_price REAL,entry_price REAL,exit_price REAL,ai_score_created REAL,model_stance TEXT,status TEXT NOT NULL,rule_followed INTEGER,reflection TEXT,created_at TEXT NOT NULL,closed_at TEXT,updated_at TEXT NOT NULL);CREATE INDEX IF NOT EXISTS idx_journal_user ON journal_entries(user_id,created_at);""")
    def _connect(self):db=sqlite3.connect(self.path);db.row_factory=sqlite3.Row;return db
    def create(self,user_id,payload):
        symbol=normalize_symbol(str(payload.get("symbol","")));thesis=str(payload.get("thesis","")).strip();thesis_type=str(payload.get("thesis_type","other")).strip()[:50]
        if len(thesis)<10:raise ApiError("Investment thesis must contain at least 10 characters.",400,"invalid_thesis")
        score=self.score_provider.get_score(symbol)["ai_score"] if self.score_provider and self.score_provider.available else None;stance="agree" if payload.get("model_stance","agree")=="agree" else "disagree";now=datetime.now(timezone.utc).isoformat();entry_id=str(uuid.uuid4())
        values=(entry_id,user_id,symbol,thesis_type,thesis,self._text(payload,"catalyst"),self._text(payload,"entry_reasoning"),self._text(payload,"risk_conditions"),self._number(payload,"target_price"),self._number(payload,"invalidation_price"),self._number(payload,"entry_price"),None,score,stance,"open",None,None,now,None,now)
        with self._connect() as db:db.execute("INSERT INTO journal_entries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",values);row=db.execute("SELECT * FROM journal_entries WHERE id=?",(entry_id,)).fetchone()
        return dict(row)
    def list(self,user_id):
        with self._connect() as db:return [dict(row) for row in db.execute("SELECT * FROM journal_entries WHERE user_id=? ORDER BY created_at DESC",(user_id,))]
    def close(self,user_id,entry_id,payload):
        exit_price=self._number(payload,"exit_price");reflection=str(payload.get("reflection","")).strip();followed=payload.get("rule_followed")
        if exit_price is None or exit_price<=0:raise ApiError("A positive exit price is required.",400,"invalid_exit_price")
        if followed not in {True,False}:raise ApiError("Record whether the thesis rules were followed.",400,"missing_rule_assessment")
        now=datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            row=db.execute("SELECT * FROM journal_entries WHERE id=? AND user_id=?",(entry_id,user_id)).fetchone()
            if not row:raise ApiError("Journal entry not found.",404,"journal_not_found")
            db.execute("UPDATE journal_entries SET exit_price=?,reflection=?,rule_followed=?,status='closed',closed_at=?,updated_at=? WHERE id=?",(exit_price,reflection,int(followed),now,now,entry_id));return dict(db.execute("SELECT * FROM journal_entries WHERE id=?",(entry_id,)).fetchone())
    def analytics(self,user_id):
        entries=self.list(user_id);closed=[entry for entry in entries if entry["status"]=="closed" and entry["entry_price"] and entry["exit_price"]]
        for entry in closed:entry["return"]=(entry["exit_price"]/entry["entry_price"])-1
        def summarize(group):return {"trades":len(group),"win_rate":sum(item["return"]>0 for item in group)/len(group) if group else None,"average_return":sum(item["return"] for item in group)/len(group) if group else None,"rule_adherence":sum(bool(item["rule_followed"]) for item in group)/len(group) if group else None}
        thesis={kind:summarize([item for item in closed if item["thesis_type"]==kind]) for kind in sorted({item["thesis_type"] for item in closed})};agreement={stance:summarize([item for item in closed if item["model_stance"]==stance]) for stance in ("agree","disagree")}
        return {"overall":summarize(closed),"by_thesis_type":thesis,"by_model_stance":agreement,"open_theses":sum(item["status"]=="open" for item in entries)}
    @staticmethod
    def _text(payload,key):value=str(payload.get(key,"")).strip();return value or None
    @staticmethod
    def _number(payload,key):
        try:return float(payload[key]) if payload.get(key) not in (None,"") else None
        except (TypeError,ValueError):raise ApiError(f"{key.replace('_',' ').title()} must be numeric.",400,"invalid_number")
