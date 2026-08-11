import React, { useEffect, useState, useRef } from 'react'
import 'chart.js/auto';
import 'chartjs-adapter-date-fns';
import {Line} from "react-chartjs-2"
import './LineGraph.css'

function LineGraph() {

    const [ graphData, setGraphData ] = useState([])
    const chartRef = useRef(null);
    const createMockData = () => {
        let data = [];
        let val = 50;
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        for(var i = 0; i < 365; i++){
            let date = new Date(today);
            date.setDate(today.getDate() - (364 - i));
            date.setHours(Math.floor(Math.random() * 24));
            date.setMinutes(Math.floor(Math.random() * 60));
            date.setSeconds(Math.floor(Math.random() * 60));
            val += Math.round((Math.random() < 0.5 ? 1 : 0) * Math.random() * 10);
            data.push({x: date, y: val});
        }
        setGraphData(data);
    }

    useEffect(()=>{
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
        <div className = "line">
            <Line 
                ref={chartRef}
                data = {{
                    datasets: [
                        {
                            type: "line",
                            data: graphData,
                            backgroundColor: "black",
                            borderColor: "#5AC53B",
                            borderWidth: 2,
                            pointBorderColor: 'rgba(0, 0, 0, 0',
                            pointBackgroundColor: 'rgba(0, 0, 0, 0',
                            pointHoverBackgroundColor: '#5AC53B',
                            pointHoverBorderColor: '#000000',
                            pointHoverBorderWidth: 4,
                            pointHoverRadius: 6,
                        }
                    ]
                }}
                options = {{
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
                            }
                        },
                        y: {
                            type: 'linear',
                            ticks: {
                                display: false
                            }
                        }
                    },
                    tooltips: {
                        mode: "index",
                        intersect: false
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    maintainAspectRatio: false
                }}
            />
        </div>
    )
}

export default LineGraph
