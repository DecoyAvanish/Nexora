from backend.services.resilience import ResilienceManager
def test_stale_cache_is_returned_when_provider_fails():
    manager=ResilienceManager();value,meta=manager.execute("test","key",lambda:{"value":1},fresh_seconds=-1,stale_seconds=60,retries=0)
    fallback,meta=manager.execute("test","key",lambda:(_ for _ in ()).throw(RuntimeError("down")),fresh_seconds=1,stale_seconds=60,retries=0)
    assert fallback==value and meta["stale"] is True
