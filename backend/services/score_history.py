"""Durable AI-score snapshots used for event attribution."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class ScoreHistoryService:
    def __init__(self, db_path="data/score_history.db"):
        self.path=Path(db_path); self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._connect() as db: db.execute("CREATE TABLE IF NOT EXISTS score_snapshots(id INTEGER PRIMARY KEY AUTOINCREMENT,symbol TEXT NOT NULL,score REAL NOT NULL,probability REAL,model_version TEXT,regime TEXT,recorded_at TEXT NOT NULL,UNIQUE(symbol,recorded_at))")
    def _connect(self):
        db=sqlite3.connect(self.path); db.row_factory=sqlite3.Row; return db
    def record(self,symbol,payload):
        now=datetime.now(timezone.utc).isoformat(); regime=payload.get("regime_adjustment",{}).get("regime",{}).get("state")
        with self._connect() as db: db.execute("INSERT OR IGNORE INTO score_snapshots(symbol,score,probability,model_version,regime,recorded_at) VALUES(?,?,?,?,?,?)",(symbol,float(payload["ai_score"]),payload.get("outperformance_probability"),payload.get("model_version"),regime,now))
    def history(self,symbol,since=None):
        query="SELECT * FROM score_snapshots WHERE symbol=?"; params=[symbol]
        if since: query+=" AND recorded_at>=?"; params.append(since)
        query+=" ORDER BY recorded_at"
        with self._connect() as db:return [dict(row) for row in db.execute(query,params)]
