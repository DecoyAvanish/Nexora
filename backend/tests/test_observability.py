from backend.services.observability import ObservabilityService
class Pipeline:
    def dashboard(self):return {"jobs":[{"job_name":"news","status":"succeeded"}],"unresolved_dead_letters":0}
def test_status_reports_latency_cache_success_and_job_health(tmp_path):
    service=ObservabilityService(tmp_path/"observability.db");service.increment("api_total",10);service.increment("api_errors",1);service.increment("cache_hit",3);service.increment("cache_miss",1);service.observe("request",20);service.observe("provider:news",50);service.mark_freshness("news","2026-11-18T12:00:00+00:00")
    result=service.status(Pipeline());assert result["api"]["success_rate"]==.9;assert result["cache"]["hit_rate"]==.75;assert result["providers"]["news"]["p95_ms"]==50;assert result["background_jobs"]["latest"][0]["status"]=="succeeded"
