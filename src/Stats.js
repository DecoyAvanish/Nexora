import React, { useEffect, useState } from 'react'
import './Stats.css'
import axios from "axios"
import StatsRow from './StatsRow'
import { database } from "./firebase";
import { collection, onSnapshot, query, where } from 'firebase/firestore';

const BASE_URL = "https://finnhub.io/api/v1/quote";
const TOKEN = "d9tj431r01qujo6kusr0d9tj431r01qujo6kusrg";

function Stats() {

  const [stockData, setStockData] = useState([])

  const getStockData = (stock) => {
    return axios
      .get(`${BASE_URL}?symbol=${stock}&token=${TOKEN}`)
      .then((res) => res.data)
      .catch((error) => {
        console.error("Error", error.message);
        return null;
      });
  }
  
  const [ myStocks, setMyStocks] = useState([])

  const getMyStocks = () => {
    const stocksCollection = collection(database, 'myStocks');
    const q = query(stocksCollection);
    
    onSnapshot(q, (snapshot) => {
      let promises = [];
      let tempData = [];
      
      snapshot.docs.map((doc) => {
        promises.push(
          getStockData(doc.data().ticker)
          .then(res => {
            tempData.push({
              id: doc.id,
              data: doc.data(),
              info: res
            });
          })
        );
      });
      
      Promise.all(promises).then(() => {
        setMyStocks(tempData);
      });
    });
  }

  useEffect(() => {
    let stockDataArray = []
    const stockList = ["AAPL", "MSFT", "TSLA", "FB", "BABA", "UBER", "DIS", "SBUX"];
    let promises = [];
    getMyStocks();
    stockList.map((stock) => {
      promises.push(
        getStockData(stock)
        .then((data) => {
          if(data) {
            stockDataArray.push({
              name: stock,
              ...data
            });
          }
        })
      )
    });

    Promise.all(promises).then(() => {
      setStockData(stockDataArray);
    })
  }, [])

  return (
    <div className = "stats">
      <div className = "container">
        <div className = "header">
          <p>Stocks</p>
        </div>
        <div className = "content">
          <div className = "rows">
            {myStocks.map((stock) => (
              <StatsRow
                key = {stock.id}
                name = {stock.data.ticker}
                openPrice = {stock.info.o}
                shares = {stock.info.v}
                price = {stock.info.c}
              />
            ))}
          </div>
        </div>
        <div className = "header list">
          <p>Lists</p>
        </div>
        <div className = "content">
          <div className = "rows">
            {stockData.map((stock) => (
              <StatsRow
                key = {stock.name}
                name = {stock.name}
                openPrice = {stock.o}
                shares = {stock.v}
                price = {stock.c}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Stats
