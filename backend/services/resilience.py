"""Redis-backed SWR cache, provider throttling, retries, and circuit breakers."""
import json,random,time
from collections import defaultdict,deque
from threading import Lock
from backend.errors import ApiError
from backend.services.news import NewsArticle

class ResilienceManager:
    def __init__(self,redis_url="",failure_threshold=3,open_seconds=60):
        self.redis=None;self.memory={};self.windows=defaultdict(deque);self.circuits=defaultdict(lambda:{"failures":0,"open_until":0});self.lock=Lock();self.failure_threshold=failure_threshold;self.open_seconds=open_seconds
        if redis_url:
            try:
                import redis
                self.redis=redis.Redis.from_url(redis_url,decode_responses=True,socket_timeout=1);self.redis.ping()
            except Exception:self.redis=None
    def execute(self,provider,key,loader,fresh_seconds=300,stale_seconds=3600,rate_per_minute=60,retries=2):
        cached=self._get(key);now=time.time()
        if cached and cached["fresh_until"]>now:return cached["value"],{"cache":"fresh","stale":False,"provider":provider}
        circuit=self.circuits[provider]
        if circuit["open_until"]>now:
            if cached and cached["stale_until"]>now:return cached["value"],{"cache":"stale","stale":True,"provider":provider,"reason":"provider_circuit_open"}
            raise ApiError(f"{provider} circuit is temporarily open.",503,"provider_circuit_open")
        self._throttle(provider,rate_per_minute)
        for attempt in range(retries+1):
            try:
                value=loader();self._set(key,value,fresh_seconds,stale_seconds);circuit["failures"]=0;return value,{"cache":"miss","stale":False,"provider":provider,"retry_count":attempt}
            except Exception as error:
                circuit["failures"]+=1
                if circuit["failures"]>=self.failure_threshold:circuit["open_until"]=time.time()+self.open_seconds
                if attempt<retries:time.sleep(min(.1*(2**attempt)+random.random()*.1,1));continue
                if cached and cached["stale_until"]>now:return cached["value"],{"cache":"stale","stale":True,"provider":provider,"reason":type(error).__name__}
                raise
    def _throttle(self,provider,limit):
        now=time.time()
        with self.lock:
            window=self.windows[provider]
            while window and window[0]<now-60:window.popleft()
            if len(window)>=limit:raise ApiError(f"{provider} rate limit reached.",429,"provider_rate_limited")
            window.append(now)
    def _get(self,key):
        try:
            raw=self.redis.get(key) if self.redis else None
            if raw:return json.loads(raw)
        except Exception:pass
        return self.memory.get(key)
    def _set(self,key,value,fresh,stale):
        record={"value":value,"fresh_until":time.time()+fresh,"stale_until":time.time()+stale};self.memory[key]=record
        if self.redis:
            try:self.redis.setex(key,stale,json.dumps(record))
            except Exception:pass

class ResilientNewsService:
    def __init__(self,service,resilience):self.service,self.resilience=service,resilience;self.last_metadata={}
    def company_news(self,symbol,company_name=None,**kwargs):
        days=kwargs.get("days",7);limit=kwargs.get("limit",25);key=f"news:{symbol.upper()}:{company_name}:{days}:{limit}"
        value,meta=self.resilience.execute("news",key,lambda:[article.to_dict() for article in self.service.company_news(symbol,company_name,**kwargs)],fresh_seconds=300,stale_seconds=3600,rate_per_minute=30);self.last_metadata=meta
        return [NewsArticle(**item) for item in value]
