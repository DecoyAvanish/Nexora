"""CLI entry point used by schedulers to run observable provider jobs."""
import argparse,os
from backend.services.market_data import MarketDataService
from backend.services.news import NewsService
from backend.services.sec_edgar import SecEdgarService
from backend.services.pipeline import PipelineOrchestrator

def build():
    pipeline=PipelineOrchestrator(os.getenv("NEXORA_PIPELINE_DB","data/pipeline.db"));market=MarketDataService();news=NewsService();sec=SecEdgarService(os.getenv("SEC_USER_AGENT","Nexora research avanishpakalapati@gmail.com"))
    pipeline.register("daily_price_ingestion",lambda payload:{"rows_processed":len(market.history(payload.get("symbol","SPY"),"1y").dates),"provider":"yfinance"})
    pipeline.register("intraday_quote_updates",lambda payload:{"rows_processed":1,"quote":market.quote_payload(market.history(payload.get("symbol","SPY"),"5d")),"provider":"yfinance"})
    pipeline.register("news_collection",lambda payload:{"rows_processed":len(news.company_news(payload.get("symbol","AAPL"),days=2,limit=75)),"provider":"gdelt_or_yahoo"})
    pipeline.register("sec_filing_ingestion",lambda payload:{"rows_processed":len(sec.recent_filings(payload.get("symbol","AAPL"),100)["filings"]),"provider":"sec_edgar"})
    for name in ("feature_generation","score_calculation","model_monitoring","model_retraining","alert_generation"):pipeline.register(name,lambda payload,name=name:{"rows_processed":0,"delegated":name,"note":"Job boundary registered; production worker supplies universe-specific payload."})
    return pipeline
def main():
    parser=argparse.ArgumentParser();parser.add_argument("job");parser.add_argument("--symbol");args=parser.parse_args();result=build().run(args.job,{"symbol":args.symbol} if args.symbol else {});print(result)
if __name__=="__main__":main()
