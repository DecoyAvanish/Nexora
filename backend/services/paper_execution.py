"""Server-owned paper execution, accounting, and immutable fill ledger."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from backend.errors import ApiError
from backend.services.market_data import normalize_symbol

ORDER_TYPES = {"market", "limit", "stop", "stop_limit"}
ORDER_STATES = {"pending", "accepted", "partially_filled", "filled", "cancelled", "rejected"}


class PaperExecutionService:
    def __init__(self, db_path="data/paper_trading.db", quote_provider=None, starting_cash=100000, slippage_bps=5, commission=0):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.quote_provider = quote_provider
        self.starting_cash = Decimal(str(starting_cash))
        self.slippage_bps = Decimal(str(slippage_bps))
        self.commission = Decimal(str(commission))
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self):
        with self._connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS accounts(user_id TEXT PRIMARY KEY,cash TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,client_order_id TEXT NOT NULL,symbol TEXT NOT NULL,side TEXT NOT NULL,type TEXT NOT NULL,quantity TEXT NOT NULL,limit_price TEXT,stop_price TEXT,status TEXT NOT NULL,rejection_reason TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(user_id,client_order_id));
            CREATE TABLE IF NOT EXISTS fills(id TEXT PRIMARY KEY,order_id TEXT NOT NULL,user_id TEXT NOT NULL,symbol TEXT NOT NULL,side TEXT NOT NULL,quantity TEXT NOT NULL,price TEXT NOT NULL,commission TEXT NOT NULL,slippage TEXT NOT NULL,executed_at TEXT NOT NULL,FOREIGN KEY(order_id) REFERENCES orders(id));
            CREATE TABLE IF NOT EXISTS ledger(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,event_type TEXT NOT NULL,amount TEXT NOT NULL,balance_after TEXT NOT NULL,reference_id TEXT NOT NULL,created_at TEXT NOT NULL,metadata TEXT NOT NULL);
            CREATE TRIGGER IF NOT EXISTS immutable_fills_update BEFORE UPDATE ON fills BEGIN SELECT RAISE(ABORT,'fills are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS immutable_fills_delete BEFORE DELETE ON fills BEGIN SELECT RAISE(ABORT,'fills are immutable'); END;
            CREATE TRIGGER IF NOT EXISTS immutable_ledger_update BEFORE UPDATE ON ledger BEGIN SELECT RAISE(ABORT,'ledger is immutable'); END;
            CREATE TRIGGER IF NOT EXISTS immutable_ledger_delete BEFORE DELETE ON ledger BEGIN SELECT RAISE(ABORT,'ledger is immutable'); END;
            """)

    def account(self, user_id):
        with self._connect() as db:
            self._ensure_account(db, user_id)
            cash = Decimal(db.execute("SELECT cash FROM accounts WHERE user_id=?", (user_id,)).fetchone()["cash"])
            positions = self._positions(db, user_id)
        market_value = sum((Decimal(str(p["market_value"])) for p in positions), Decimal("0"))
        return {"cash": float(cash), "buying_power": float(cash), "portfolio_value": float(cash + market_value), "positions": positions, "paper_only": True}

    def place_order(self, user_id, payload):
        symbol = normalize_symbol(str(payload.get("symbol", "")))
        side, order_type = payload.get("side"), payload.get("type", "market")
        if side not in {"buy", "sell"} or order_type not in ORDER_TYPES: raise ApiError("Invalid order side or type.", 400, "invalid_order")
        quantity = self._decimal(payload.get("quantity"), "quantity")
        if quantity <= 0: raise ApiError("Quantity must be positive.", 400, "invalid_quantity")
        limit_price = self._optional_price(payload.get("limit_price")); stop_price = self._optional_price(payload.get("stop_price"))
        if order_type in {"limit", "stop_limit"} and limit_price is None: raise ApiError("A limit price is required.", 400, "missing_limit_price")
        if order_type in {"stop", "stop_limit"} and stop_price is None: raise ApiError("A stop price is required.", 400, "missing_stop_price")
        client_id = str(payload.get("client_order_id") or uuid.uuid4())[:80]
        now, order_id = self._now(), str(uuid.uuid4())
        price = self._quote(symbol)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE"); self._ensure_account(db, user_id)
            existing = db.execute("SELECT * FROM orders WHERE user_id=? AND client_order_id=?", (user_id, client_id)).fetchone()
            if existing: return self._order(existing)
            rejection = self._validate_balance(db, user_id, symbol, side, quantity, limit_price or price)
            status = "rejected" if rejection else "accepted"
            db.execute("INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (order_id,user_id,client_id,symbol,side,order_type,str(quantity),self._str(limit_price),self._str(stop_price),status,rejection,now,now))
            should_fill = not rejection and self._executable(side, order_type, price, limit_price, stop_price)
            if should_fill: self._fill(db, order_id, user_id, symbol, side, quantity, price)
            row = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        return self._order(row)

    def cancel(self, user_id, order_id):
        with self._connect() as db:
            row = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (order_id,user_id)).fetchone()
            if not row: raise ApiError("Order not found.", 404, "order_not_found")
            if row["status"] not in {"pending","accepted","partially_filled"}: raise ApiError("This order can no longer be cancelled.", 409, "invalid_order_state")
            db.execute("UPDATE orders SET status='cancelled',updated_at=? WHERE id=?", (self._now(),order_id))
            return self._order(db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone())

    def orders(self, user_id):
        with self._connect() as db: return [self._order(r) for r in db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC",(user_id,))]
    def ledger(self, user_id):
        with self._connect() as db: return [{**dict(r),"metadata":json.loads(r["metadata"])} for r in db.execute("SELECT * FROM ledger WHERE user_id=? ORDER BY created_at DESC",(user_id,))]

    def _fill(self, db, order_id, user_id, symbol, side, quantity, reference_price):
        direction = Decimal("1") if side == "buy" else Decimal("-1")
        slippage = reference_price * self.slippage_bps / Decimal("10000")
        price = (reference_price + direction * slippage).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        cash_delta = -(price * quantity + self.commission) if side == "buy" else price * quantity - self.commission
        current = Decimal(db.execute("SELECT cash FROM accounts WHERE user_id=?",(user_id,)).fetchone()["cash"])
        balance = current + cash_delta; fill_id = str(uuid.uuid4()); now = self._now()
        db.execute("INSERT INTO fills VALUES(?,?,?,?,?,?,?,?,?,?)",(fill_id,order_id,user_id,symbol,side,str(quantity),str(price),str(self.commission),str(abs(slippage)),now))
        db.execute("UPDATE accounts SET cash=? WHERE user_id=?",(str(balance),user_id))
        db.execute("UPDATE orders SET status='filled',updated_at=? WHERE id=?",(now,order_id))
        db.execute("INSERT INTO ledger VALUES(?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),user_id,"trade_fill",str(cash_delta),str(balance),fill_id,now,json.dumps({"symbol":symbol,"side":side,"quantity":str(quantity),"price":str(price)})))

    def _positions(self, db, user_id):
        fills = db.execute("SELECT * FROM fills WHERE user_id=? ORDER BY executed_at,id",(user_id,)).fetchall(); state={}
        for fill in fills:
            item=state.setdefault(fill["symbol"],{"quantity":Decimal("0"),"cost":Decimal("0"),"realized":Decimal("0")}); qty=Decimal(fill["quantity"]); price=Decimal(fill["price"])
            if fill["side"]=="buy": item["cost"] += qty*price; item["quantity"] += qty
            elif item["quantity"]:
                average=item["cost"]/item["quantity"]; item["realized"] += qty*(price-average); item["quantity"]-=qty; item["cost"]-=qty*average
        result=[]
        for symbol,item in state.items():
            if item["quantity"]<=0: continue
            average=item["cost"]/item["quantity"]; market=self._quote(symbol); unrealized=(market-average)*item["quantity"]
            result.append({"symbol":symbol,"quantity":float(item["quantity"]),"average_cost":float(average),"market_price":float(market),"market_value":float(market*item["quantity"]),"realized_pnl":float(item["realized"]),"unrealized_pnl":float(unrealized)})
        return result

    def _validate_balance(self, db,user,symbol,side,qty,price):
        if side=="buy":
            cash=Decimal(db.execute("SELECT cash FROM accounts WHERE user_id=?",(user,)).fetchone()["cash"])
            if qty*price+self.commission>cash: return "insufficient_buying_power"
        else:
            owned=sum((Decimal(r["quantity"]) * (1 if r["side"]=="buy" else -1) for r in db.execute("SELECT side,quantity FROM fills WHERE user_id=? AND symbol=?",(user,symbol))),Decimal("0"))
            if qty>owned: return "insufficient_shares"
        return None
    def _ensure_account(self,db,user): db.execute("INSERT OR IGNORE INTO accounts VALUES(?,?,?)",(user,str(self.starting_cash),self._now()))
    def _quote(self,symbol):
        if callable(self.quote_provider): return Decimal(str(self.quote_provider(symbol)))
        if self.quote_provider: return Decimal(str(self.quote_provider.history(symbol,"5d").last_price))
        raise ApiError("A quote provider is required.",503,"quote_unavailable")
    @staticmethod
    def _executable(side,kind,price,limit,stop):
        triggered = stop is None or (price>=stop if side=="buy" else price<=stop)
        return triggered and (kind in {"market","stop"} or (price<=limit if side=="buy" else price>=limit))
    @staticmethod
    def _decimal(value,name):
        try: return Decimal(str(value))
        except (InvalidOperation,TypeError): raise ApiError(f"Invalid {name}.",400,f"invalid_{name}")
    def _optional_price(self,value): return None if value in (None,"") else self._decimal(value,"price")
    @staticmethod
    def _str(value): return str(value) if value is not None else None
    @staticmethod
    def _now(): return datetime.now(timezone.utc).isoformat()
    @staticmethod
    def _order(row):
        value=dict(row); value["quantity"]=float(value["quantity"])
        for key in ("limit_price","stop_price"): value[key]=float(value[key]) if value[key] is not None else None
        value["paper_only"]=True; return value
