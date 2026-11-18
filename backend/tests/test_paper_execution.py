from backend.services.paper_execution import PaperExecutionService


def test_idempotent_orders_and_fill_derived_positions(tmp_path):
    service = PaperExecutionService(tmp_path / "paper.db", lambda _symbol: 100, starting_cash=1000, slippage_bps=0)
    payload = {"symbol":"AAPL","side":"buy","type":"market","quantity":2.5,"client_order_id":"same-request"}
    first = service.place_order("user-1", payload)
    second = service.place_order("user-1", payload)
    assert first["id"] == second["id"]
    assert first["status"] == "filled"
    account = service.account("user-1")
    assert account["cash"] == 750
    assert account["positions"][0]["quantity"] == 2.5
    assert len(service.ledger("user-1")) == 1


def test_server_rejects_orders_above_buying_power(tmp_path):
    service = PaperExecutionService(tmp_path / "paper.db", lambda _symbol: 100, starting_cash=50)
    result = service.place_order("user-1", {"symbol":"AAPL","side":"buy","type":"market","quantity":1})
    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "insufficient_buying_power"
