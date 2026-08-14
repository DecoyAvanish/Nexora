import React, { useEffect, useState } from 'react';
import './Stats.css';
import axios from 'axios';
import StatsRow from './StatsRow';
import { database, auth, doc, onSnapshot } from './firebase';

const FINNHUB_TOKEN = "d9tj431r01qujo6kusr0d9tj431r01qujo6kusrg";

function Stats() {
  const [stockData, setStockData] = useState([]);
  const [myStocks, setMyStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalPortfolioValue, setTotalPortfolioValue] = useState(0);
  const [cashBalance, setCashBalance] = useState(0);

  const getStockData = async (stock) => {
    try {
      const response = await axios.get(
        `https://finnhub.io/api/v1/quote?symbol=${stock}&token=${FINNHUB_TOKEN}`
      );
      return response.data;
    } catch (error) {
      console.error(`Error fetching ${stock}:`, error.message);
      return null;
    }
  };

  useEffect(() => {
    if (!auth.currentUser) {
      setLoading(false);
      return;
    }

    const userRef = doc(database, 'users', auth.currentUser.uid);
    
    const unsubscribe = onSnapshot(userRef, async (doc) => {
      if (doc.exists()) {
        const data = doc.data();
        const holdings = data.portfolio?.holdings || [];
        const cash = data.portfolio?.cash || 0;
        setCashBalance(cash);
        
        let tempData = [];
        let totalValue = cash;
        
        for (const holding of holdings) {
          const quote = await getStockData(holding.symbol);
          if (quote && quote.c) {
            const currentPrice = quote.c;
            const value = currentPrice * holding.shares;
            totalValue += value;
            
            tempData.push({
              id: holding.symbol,
              data: {
                ticker: holding.symbol,
                shares: holding.shares,
                avgPrice: holding.avgPrice
              },
              info: {
                c: currentPrice,
                pc: holding.avgPrice,
                o: quote.o || currentPrice,
                h: quote.h || currentPrice,
                l: quote.l || currentPrice,
                d: quote.d || 0,
                dp: quote.dp || 0
              }
            });
          }
        }
        
        setMyStocks(tempData);
        setTotalPortfolioValue(totalValue);
        setLoading(false);
      } else {
        setLoading(false);
      }
    });

    return () => unsubscribe();
  }, []);

  useEffect(() => {
    const fetchMarketData = async () => {
      const stockList = ["AAPL", "MSFT", "TSLA", "META", "BABA", "UBER", "DIS", "SBUX"];
      let promises = [];
      let tempData = [];

      stockList.forEach((stock) => {
        promises.push(
          getStockData(stock)
            .then((data) => {
              if (data && data.c) {
                tempData.push({
                  name: stock,
                  c: data.c,
                  pc: data.pc || data.c,
                  o: data.o || data.c,
                  h: data.h || data.c,
                  l: data.l || data.c,
                  d: data.d || 0,
                  dp: data.dp || 0
                });
              }
            })
        );
      });

      await Promise.all(promises);
      setStockData(tempData);
    };

    fetchMarketData();
  }, []);

  return (
    <div className="stats">
      <div className="container">
        <div className="header">
          <p>MY STOCKS</p>
          <span>●</span>
        </div>
        <div className="content">
          <div className="rows">
            {loading ? (
              <div style={{ padding: '20px', textAlign: 'center', color: 'rgba(240,237,255,0.2)', fontSize: '11px', fontFamily: "'IBM Plex Mono', monospace" }}>
                Loading...
              </div>
            ) : myStocks.length > 0 ? (
              <>
                <div style={{ 
                  padding: '12px 16px', 
                  background: 'rgba(168, 85, 247, 0.03)', 
                  borderBottom: '1px solid rgba(168, 85, 247, 0.04)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: '11px',
                  color: 'rgba(240, 237, 255, 0.4)'
                }}>
                  <span>Total Value</span>
                  <span style={{ color: '#A855F7', fontWeight: '700', fontSize: '14px' }}>
                    ${totalPortfolioValue.toFixed(2)}
                  </span>
                </div>
                <div style={{ 
                  padding: '8px 16px', 
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: '9px',
                  color: 'rgba(240, 237, 255, 0.2)',
                  borderBottom: '1px solid rgba(168, 85, 247, 0.02)'
                }}>
                  <span>Cash: ${cashBalance.toFixed(2)}</span>
                  <span>{myStocks.length} positions</span>
                </div>
                {myStocks.map((stock) => (
                  <StatsRow
                    key={stock.id}
                    name={stock.data.ticker}
                    price={stock.info?.c || 0}
                    previousClose={stock.info?.pc || stock.data.avgPrice || 0}
                    openPrice={stock.info?.o || 0}
                    shares={stock.data.shares || 0}
                  />
                ))}
              </>
            ) : (
              <div style={{ padding: '20px', textAlign: 'center', color: 'rgba(240,237,255,0.2)', fontSize: '11px', fontFamily: "'IBM Plex Mono', monospace" }}>
                No stocks in portfolio
                <div style={{ fontSize: '9px', marginTop: '8px', color: 'rgba(240,237,255,0.1)' }}>
                  Cash: ${cashBalance.toFixed(2)}
                </div>
                <div style={{ fontSize: '9px', marginTop: '4px', color: 'rgba(240,237,255,0.08)' }}>
                  Buy stocks from the Stocks tab
                </div>
              </div>
            )}
          </div>
        </div>
        <div className="header list">
          <p>MARKET</p>
          <span>●</span>
        </div>
        <div className="content">
          <div className="rows">
            {stockData.map((stock) => (
              <StatsRow
                key={stock.name}
                name={stock.name}
                price={stock.c || 0}
                previousClose={stock.pc || 0}
                openPrice={stock.o || 0}
                shares={0}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Stats;