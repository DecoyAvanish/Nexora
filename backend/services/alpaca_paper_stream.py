"""Optional Alpaca paper-only WebSocket trade-update consumer."""

import json
from urllib.parse import urlparse

from backend.errors import ApiError

PAPER_REST = "https://paper-api.alpaca.markets"
PAPER_STREAM = "wss://paper-api.alpaca.markets/stream"


class AlpacaPaperStream:
    """Consumes Alpaca `trade_updates`; deliberately refuses every live endpoint."""
    def __init__(self, api_key, secret, on_update, stream_url=PAPER_STREAM, rest_url=PAPER_REST):
        if urlparse(stream_url).hostname != "paper-api.alpaca.markets" or urlparse(rest_url).hostname != "paper-api.alpaca.markets":
            raise ApiError("Live-money Alpaca endpoints are forbidden.", 400, "paper_only_guard")
        self.api_key, self.secret, self.on_update, self.stream_url = api_key, secret, on_update, stream_url

    def run_forever(self):
        try:
            import websocket
        except ImportError as error:
            raise RuntimeError("Install websocket-client to enable Alpaca streaming.") from error
        def opened(ws):
            ws.send(json.dumps({"action":"auth","key":self.api_key,"secret":self.secret}))
            ws.send(json.dumps({"action":"listen","data":{"streams":["trade_updates"]}}))
        def message(_ws, raw):
            event=json.loads(raw)
            if event.get("stream")=="trade_updates": self.on_update(event["data"])
        websocket.WebSocketApp(self.stream_url, on_open=opened, on_message=message).run_forever(ping_interval=20)
