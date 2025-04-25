import React, { useState, useEffect } from 'react';
import { LineChart, Line, PieChart, Pie, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell } from 'recharts';

const GraphComponent = ({ logsChartData, pieData, alertChartData, anomaliesChartData, type }) => {
    const [dimensions, setDimensions] = useState({
        width: window.innerWidth * 0.8,
        height: window.innerHeight * 0.4,
    });

    useEffect(() => {
        const handleResize = () => {
            setDimensions({
                width: window.innerWidth * 0.8,
                height: window.innerHeight * 0.4,
            });
        };

        window.addEventListener('resize', handleResize);
        handleResize(); // Llamar inicialmente

        return () => window.removeEventListener('resize', handleResize);
    }, []);

    if (type === 'logs') {
        if (logsChartData && Array.isArray(logsChartData) && logsChartData.length > 0) {
            return (
                <LineChart width={dimensions.width} height={dimensions.height} data={logsChartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="count" stroke="#8884d8" />
                </LineChart>
            );
        }
        return <p>No data available for Logs chart.</p>;
    }

    if (type === 'threats') {
        if (pieData && Array.isArray(pieData) && pieData.length > 0) {
            return (
                <PieChart width={dimensions.width} height={dimensions.height}>
                    <Pie data={pieData} dataKey="value" nameKey="name" cx={dimensions.width / 2} cy={dimensions.height / 2} outerRadius={80} fill="#8884d8" label>
                        {pieData.map((entry, index) => (
                            <Cell key={`cell-${entry.name}-${index}`} fill={entry.color || '#8884d8'} />
                        ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                </PieChart>
            );
        }
        return <p>No data available for Threats chart.</p>;
    }

    if (type === 'alerts') {
        if (alertChartData && Array.isArray(alertChartData) && alertChartData.length > 0) {
            return (
                <BarChart width={dimensions.width} height={dimensions.height} data={alertChartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="ip" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="failedAttempts" fill="#82ca9d" />
                </BarChart>
            );
        }
        return <p>No data available for Alerts chart.</p>;
    }

    if (type === 'anomalies') {
        if (anomaliesChartData && Array.isArray(anomaliesChartData) && anomaliesChartData.length > 0) {
            return (
                <LineChart width={dimensions.width} height={dimensions.height} data={anomaliesChartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="count" stroke="#ff7300" />
                </LineChart>
            );
        }
        return <p>No data available for Anomalies chart.</p>;
    }

    return null;
};

export default GraphComponent;