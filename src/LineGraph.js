import React, { useEffect, useState, useRef } from 'react'
import 'chart.js/auto';
import 'chartjs-adapter-date-fns';
import { Line } from "react-chartjs-2"
import './LineGraph.css'

function LineGraph() {
  const [graphData, setGraphData] = useState([])
  const chartRef = useRef(null);

  const createMockData = () => {
    let data = [];
    let val = 100;
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (var i = 0; i < 365; i++) {
      let date = new Date(today);
      date.setDate(today.getDate() - (364 - i));
      date.setHours(Math.floor(Math.random() * 24));
      date.setMinutes(Math.floor(Math.random() * 60));
      date.setSeconds(Math.floor(Math.random() * 60));
      val += Math.round((Math.random() < 0.5 ? 1 : 0) * Math.random() * 8);
      data.push({ x: date, y: Math.max(val, 30) });
    }
    setGraphData(data);
  }

  useEffect(() => {
    createMockData();
  }, [])

  useEffect(() => {
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, []);

  return (
    <div className="line">
      <Line 
        ref={chartRef}
        data={{
          datasets: [
            {
              type: "line",
              data: graphData,
              backgroundColor: "transparent",
              borderColor: "#A855F7",
              borderWidth: 2,
              pointBorderColor: 'rgba(0, 0, 0, 0)',
              pointBackgroundColor: 'rgba(0, 0, 0, 0)',
              pointHoverBackgroundColor: '#A855F7',
              pointHoverBorderColor: '#080a11',
              pointHoverBorderWidth: 4,
              pointHoverRadius: 8,
              tension: 0.4,
            }
          ]
        }}
        options={{
          scales: {
            x: {
              type: 'time',
              time: {
                unit: 'month',
                displayFormats: {
                  month: 'MMM yy'
                }
              },
              ticks: {
                display: false
              },
              grid: {
                display: false
              }
            },
            y: {
              type: 'linear',
              ticks: {
                display: false
              },
              grid: {
                display: false
              }
            }
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              enabled: false
            }
          },
          maintainAspectRatio: false,
          interaction: {
            intersect: false,
            mode: 'index'
          }
        }}
      />
    </div>
  )
}

export default LineGraph