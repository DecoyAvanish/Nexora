from backend.services.fred import FRED_OBSERVATIONS,FredService


class Response:
    def raise_for_status(self): pass
    def json(self): return {"observations":[{"date":"2020-01-01","value":"1.5","realtime_start":"2020-02-01","realtime_end":"2020-12-31"}]}


class Session:
    def __init__(self): self.params=None
    def get(self,url,params,timeout): self.params=params; assert url==FRED_OBSERVATIONS; return Response()


def test_fred_requests_exact_alfred_vintage(tmp_path):
    session=Session(); service=FredService("key",cache_root=tmp_path,session=session)
    values=service.observations("CPIAUCSL","2020-06-15")
    assert session.params["realtime_start"]=="2020-06-15"
    assert session.params["realtime_end"]=="2020-06-15"
    assert values[0]["vintage_start"]=="2020-02-01"
