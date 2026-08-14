import React, { useEffect, useState } from 'react';
import './Stats.css';
import axios from 'axios';
import StatsRow from './StatsRow';
import { database } from './firebase';
import { collection, onSnapshot, query } from 'firebase/firestore';

const FINNHUB_TOKEN = "d9tj431r01qujo6kusr0d9tj431r01qujo6kusrg";

function Stats() {
  const [stockData, setStockData] = useState([]);
  const [myStocks, setMyStocks] = useState([]);
  const [loading, setLoading] = useState(true);

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

  const getMyStocks = () => {
    const stocksCollection = collection(database, 'myStocks');
    const q = query(stocksCollection);
    
    onSnapshot(q, async (snapshot) => {
      let promises = [];
      let tempData = [];
      
      snapshot.docs.forEach((doc) => {
        promises.push(
          getStockData(doc.data().ticker)
            .then(res => {
              if (res) {
                tempData.push({
                  id: doc.id,
                  data: doc.data(),
                  info: res
                });
              }
            })
        );
      });
      
      await Promise.all(promises);
      setMyStocks(tempData);
      setLoading(false);
    });
  };

  useEffect(() => {
    const fetchMarketData = async () => {
      const stockList = ["AAPL", "MSFT", "TSLA", "META", "BABA", "UBER", "DIS", "SBUX"];
      let promises = [];
      let tempData = [];

      stockList.forEach((stock) => {
        promises.push(
          getStockData(stock)
            .then((data) => {
              if (data) {
                tempData.push({
                  name: stock,
                  c: data.c,
                  pc: data.pc,
                  o: data.o,
                  h: data.h,
                  l: data.l,
                  d: data.d,
                  dp: data.dp 
                });
              }
            })
        );
      });

      await Promise.all(promises);
      setStockData(tempData);
    };

    getMyStocks();
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
              myStocks.map((stock) => (
                <StatsRow
                  key={stock.id}
                  name={stock.data.ticker}
                  price={stock.info.c || stock.info.pc || 0}
                  previousClose={stock.info.pc || stock.info.o || 0}
                  openPrice={stock.info.o || 0}
                  shares={stock.data.shares || 0}
                />
              ))
            ) : (
              <div style={{ padding: '20px', textAlign: 'center', color: 'rgba(240,237,255,0.2)', fontSize: '11px', fontFamily: "'IBM Plex Mono', monospace" }}>
                No stocks in portfolio
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
                price={stock.c || stock.pc || 0}
                previousClose={stock.pc || stock.o || 0}
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