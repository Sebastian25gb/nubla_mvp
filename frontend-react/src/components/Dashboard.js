import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import PaginatedTable from './PaginatedTable';
import GraphComponent from './GraphComponent';
import '../App.css';

const Dashboard = () => {
    const [logs, setLogs] = useState([]);
    const [threats, setThreats] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [anomalies, setAnomalies] = useState([]);
    const [tenants, setTenants] = useState([]);
    const [selectedTenant, setSelectedTenant] = useState('');
    const [error, setError] = useState(null);
    const [logsTotal, setLogsTotal] = useState(0);
    const [threatsTotal, setThreatsTotal] = useState(0);
    const [alertsTotal, setAlertsTotal] = useState(0);
    const [anomaliesTotal, setAnomaliesTotal] = useState(0);
    const [filter, setFilter] = useState('');
    const [logsChartData, setLogsChartData] = useState([]);
    const [pieData, setPieData] = useState([]);
    const [alertChartData, setAlertChartData] = useState([]);
    const [anomaliesChartData, setAnomaliesChartData] = useState([]);
    const [activeTab, setActiveTab] = useState('logs'); // Pestaña activa
    const [summary, setSummary] = useState(null); // Estadísticas generales

    const abortControllerRef = useRef(null);

    useEffect(() => {
        abortControllerRef.current = new AbortController();

        const fetchTenants = async () => {
            try {
                const response = await axios.get('http://localhost:8000/tenants', {
                    signal: abortControllerRef.current.signal
                });
                setTenants(response.data.tenants || []);
                if (response.data.tenants && response.data.tenants.length > 0) {
                    setSelectedTenant(response.data.tenants[0].id);
                }
            } catch (error) {
                if (axios.isCancel(error)) return;
                setError(`Failed to load tenants: ${error.response?.status || ''} ${error.message}`);
            }
        };
        fetchTenants();

        return () => {
            abortControllerRef.current.abort();
        };
    }, []);

    useEffect(() => {
        // Cargar estadísticas generales cuando cambie el tenant
        const fetchSummary = async () => {
            if (!selectedTenant) return;
            try {
                const [logsRes, threatsRes, alertsRes, anomaliesRes] = await Promise.all([
                    axios.get(`http://localhost:8000/logs/${selectedTenant}`, { params: { from: 0, size: 0 }, signal: abortControllerRef.current.signal }),
                    axios.get(`http://localhost:8000/threats/${selectedTenant}`, { params: { from: 0, size: 0 }, signal: abortControllerRef.current.signal }),
                    axios.get(`http://localhost:8000/alerts/${selectedTenant}`, { params: { from: 0, size: 0 }, signal: abortControllerRef.current.signal }),
                    axios.get(`http://localhost:8000/anomalies/${selectedTenant}`, { params: { from: 0, size: 0 }, signal: abortControllerRef.current.signal }),
                ]);
                setSummary({
                    logs: logsRes.data.total || 0,
                    threats: threatsRes.data.total || 0,
                    alerts: alertsRes.data.total || 0,
                    anomalies: anomaliesRes.data.total || 0,
                });
            } catch (error) {
                if (axios.isCancel(error)) return;
                setError(`Failed to load summary: ${error.response?.status || ''} ${error.message}`);
            }
        };

        if (selectedTenant) {
            fetchSummary();
            // Cargar datos iniciales para la pestaña activa
            if (activeTab === 'logs') fetchLogs();
            else if (activeTab === 'threats') fetchThreats();
            else if (activeTab === 'alerts') fetchAlerts();
            else if (activeTab === 'anomalies') fetchAnomalies();
        }
    }, [selectedTenant]);

    const resetState = () => {
        setLogs([]);
        setThreats([]);
        setAlerts([]);
        setAnomalies([]);
        setLogsTotal(0);
        setThreatsTotal(0);
        setAlertsTotal(0);
        setAnomaliesTotal(0);
        setFilter('');
        setLogsChartData([]);
        setPieData([]);
        setAlertChartData([]);
        setAnomaliesChartData([]);
    };

    const fetchLogs = useCallback(async (from = 0, size = 50) => {
        if (!selectedTenant) return;
        try {
            const response = await axios.get(`http://localhost:8000/logs/${selectedTenant}`, {
                params: { from, size },
                signal: abortControllerRef.current.signal
            });
            if (!response.data || typeof response.data !== 'object') {
                throw new Error('Invalid response format');
            }
            setLogs(prevLogs => {
                if (from === 0) {
                    return Array.isArray(response.data.logs) ? response.data.logs : [];
                }
                return [...prevLogs, ...(Array.isArray(response.data.logs) ? response.data.logs : [])];
            });
            setLogsTotal(typeof response.data.total === 'number' ? response.data.total : 0);
            setThreats([]);
            setAlerts([]);
            setAnomalies([]);
            setPieData([]);
            setAlertChartData([]);
            setAnomaliesChartData([]);
            setError(null);

            try {
                const statsResponse = await axios.get(`http://localhost:8000/logs-stats/${selectedTenant}`, {
                    params: { from: 0, size: 5000 },
                    signal: abortControllerRef.current.signal
                });
                setLogsChartData(Array.isArray(statsResponse.data.logs_chart_data) ? statsResponse.data.logs_chart_data : []);
            } catch (statsError) {
                if (axios.isCancel(statsError)) return;
                setLogsChartData([]);
            }
        } catch (error) {
            if (axios.isCancel(error)) return;
            setError(`Failed to load logs: ${error.response?.status || ''} ${error.message}`);
        }
    }, [selectedTenant]);

    const fetchThreats = useCallback(async (from = 0, size = 50) => {
        if (!selectedTenant) return;
        try {
            const response = await axios.get(`http://localhost:8000/threats/${selectedTenant}`, {
                params: { from, size },
                signal: abortControllerRef.current.signal
            });
            if (!response.data || typeof response.data !== 'object') {
                throw new Error('Invalid response format');
            }
            setThreats(prevThreats => {
                if (from === 0) {
                    return Array.isArray(response.data.threats) ? response.data.threats : [];
                }
                return [...prevThreats, ...(Array.isArray(response.data.threats) ? response.data.threats : [])];
            });
            setThreatsTotal(typeof response.data.total === 'number' ? response.data.total : 0);
            setLogs([]);
            setAlerts([]);
            setAnomalies([]);
            setLogsChartData([]);
            setAlertChartData([]);
            setAnomaliesChartData([]);

            try {
                const statsResponse = await axios.get(`http://localhost:8000/threats-stats/${selectedTenant}`, {
                    params: { from: 0, size: 5000 },
                    signal: abortControllerRef.current.signal
                });
                setPieData(Array.isArray(statsResponse.data.pie_data) ? statsResponse.data.pie_data : []);
            } catch (statsError) {
                if (axios.isCancel(statsError)) return;
                setPieData([]);
            }
            setError(null);
        } catch (error) {
            if (axios.isCancel(error)) return;
            setError(`Failed to load threats: ${error.response?.status || ''} ${error.message}`);
        }
    }, [selectedTenant]);

    const fetchAlerts = useCallback(async (from = 0, size = 50) => {
        if (!selectedTenant) return;
        try {
            const response = await axios.get(`http://localhost:8000/alerts/${selectedTenant}`, {
                params: { from, size },
                signal: abortControllerRef.current.signal
            });
            if (!response.data || typeof response.data !== 'object') {
                throw new Error('Invalid response format');
            }
            const formattedAlerts = Array.isArray(response.data.alerts) ? response.data.alerts.map((alert, index) => ({
                timestamp: new Date().toISOString(),
                tenant: selectedTenant,
                message: `${alert.ip} (${alert.count} fails)`,
                status: "Alert"
            })) : [];
            setAlerts(prevAlerts => {
                if (from === 0) {
                    return formattedAlerts;
                }
                return [...prevAlerts, ...formattedAlerts];
            });
            setAlertsTotal(typeof response.data.total === 'number' ? response.data.total : 0);
            setLogs([]);
            setThreats([]);
            setAnomalies([]);
            setLogsChartData([]);
            setPieData([]);
            setAnomaliesChartData([]);

            try {
                const statsResponse = await axios.get(`http://localhost:8000/alerts-stats/${selectedTenant}`, {
                    params: { from: 0, size: 5000 },
                    signal: abortControllerRef.current.signal
                });
                setAlertChartData(Array.isArray(statsResponse.data.alert_chart_data) ? statsResponse.data.alert_chart_data : []);
            } catch (statsError) {
                if (axios.isCancel(statsError)) return;
                setAlertChartData([]);
            }
            setError(null);
        } catch (error) {
            if (axios.isCancel(error)) return;
            setError(`Failed to load alerts: ${error.response?.status || ''} ${error.message}`);
        }
    }, [selectedTenant]);

    const fetchAnomalies = useCallback(async (from = 0, size = 50) => {
        if (!selectedTenant) return;
        try {
            const response = await axios.get(`http://localhost:8000/anomalies/${selectedTenant}`, {
                params: { from, size },
                signal: abortControllerRef.current.signal
            });
            if (!response.data || typeof response.data !== 'object') {
                throw new Error('Invalid response format');
            }
            const anomaliesData = Array.isArray(response.data.anomalies) ? response.data.anomalies : [];
            setAnomalies(prevAnomalies => {
                if (from === 0) {
                    return anomaliesData;
                }
                return [...prevAnomalies, ...anomaliesData];
            });
            setAnomaliesTotal(typeof response.data.total === 'number' ? response.data.total : 0);
            setLogs([]);
            setThreats([]);
            setAlerts([]);
            setLogsChartData([]);
            setPieData([]);
            setAlertChartData([]);
            setError(null);

            const anomaliesByHour = anomaliesData.reduce((acc, anomaly) => {
                if (!anomaly || !anomaly.timestamp) return acc;
                const hour = new Date(anomaly.timestamp).getHours();
                acc[hour] = (acc[hour] || 0) + 1;
                return acc;
            }, {});
            const anomaliesChartData = Object.keys(anomaliesByHour).map(hour => ({
                hour: `${hour}:00`,
                count: anomaliesByHour[hour]
            }));
            setAnomaliesChartData(anomaliesChartData);
        } catch (error) {
            if (axios.isCancel(error)) return;
            setError(`Failed to load anomalies: ${error.response?.status || ''} ${error.message}`);
            setAnomaliesChartData([]);
        }
    }, [selectedTenant]);

    const handleTabChange = (tab) => {
        setActiveTab(tab);
        resetState();
        if (tab === 'logs') fetchLogs();
        else if (tab === 'threats') fetchThreats();
        else if (tab === 'alerts') fetchAlerts();
        else if (tab === 'anomalies') fetchAnomalies();
    };

    return (
        <div className="dashboard">
            {error && <p style={{ color: 'red' }}>{error}</p>}
            <div className="header">
                <h1>Nubla MVP SIEM Dashboard</h1>
                <div className="controls">
                    <select
                        value={selectedTenant}
                        onChange={(e) => { setSelectedTenant(e.target.value); resetState(); setActiveTab('logs'); }}
                    >
                        <option value="">Select Tenant</option>
                        {tenants.map(tenant => (
                            <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
                        ))}
                    </select>
                    <input
                        type="text"
                        placeholder="Filter logs (local data only)..."
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                    />
                </div>
            </div>
            {summary && (
                <div className="summary">
                    <h2>Summary for {selectedTenant}</h2>
                    <div className="summary-stats">
                        <div className="stat">
                            <strong>Total Logs:</strong> {summary.logs}
                        </div>
                        <div className="stat">
                            <strong>Total Threats:</strong> {summary.threats}
                        </div>
                        <div className="stat">
                            <strong>Total Alerts:</strong> {summary.alerts}
                        </div>
                        <div className="stat">
                            <strong>Total Anomalies:</strong> {summary.anomalies}
                        </div>
                    </div>
                </div>
            )}
            <div className="tabs">
                <button
                    className={activeTab === 'logs' ? 'active' : ''}
                    onClick={() => handleTabChange('logs')}
                    disabled={!selectedTenant}
                >
                    Logs
                </button>
                <button
                    className={activeTab === 'threats' ? 'active' : ''}
                    onClick={() => handleTabChange('threats')}
                    disabled={!selectedTenant}
                >
                    Threats
                </button>
                <button
                    className={activeTab === 'alerts' ? 'active' : ''}
                    onClick={() => handleTabChange('alerts')}
                    disabled={!selectedTenant}
                >
                    Alerts
                </button>
                <button
                    className={activeTab === 'anomalies' ? 'active' : ''}
                    onClick={() => handleTabChange('anomalies')}
                    disabled={!selectedTenant}
                >
                    Anomalies
                </button>
            </div>
            <div className="content">
                {activeTab === 'logs' && (
                    <>
                        <div className="table-section">
                            <PaginatedTable
                                logs={logs}
                                title="Logs"
                                type="logs"
                                total={logsTotal}
                                fetchData={fetchLogs}
                                filter={filter}
                                onError={setError}
                            />
                        </div>
                        <div className="chart-section">
                            <GraphComponent
                                logsChartData={logsChartData}
                                pieData={[]}
                                alertChartData={[]}
                                anomaliesChartData={[]}
                                type="logs"
                            />
                        </div>
                    </>
                )}
                {activeTab === 'threats' && (
                    <>
                        <div className="table-section">
                            <PaginatedTable
                                logs={threats}
                                title="Threats"
                                type="threats"
                                total={threatsTotal}
                                fetchData={fetchThreats}
                                filter={filter}
                                onError={setError}
                            />
                        </div>
                        <div className="chart-section">
                            <GraphComponent
                                logsChartData={[]}
                                pieData={pieData}
                                alertChartData={[]}
                                anomaliesChartData={[]}
                                type="threats"
                            />
                        </div>
                    </>
                )}
                {activeTab === 'alerts' && (
                    <>
                        <div className="table-section">
                            <PaginatedTable
                                logs={alerts}
                                title="Alerts"
                                type="alerts"
                                total={alertsTotal}
                                fetchData={fetchAlerts}
                                filter={filter}
                                onError={setError}
                            />
                        </div>
                        <div className="chart-section">
                            <GraphComponent
                                logsChartData={[]}
                                pieData={[]}
                                alertChartData={alertChartData}
                                anomaliesChartData={[]}
                                type="alerts"
                            />
                        </div>
                    </>
                )}
                {activeTab === 'anomalies' && (
                    <>
                        <div className="table-section">
                            <PaginatedTable
                                logs={anomalies}
                                title="Anomalies"
                                type="anomalies"
                                total={anomaliesTotal}
                                fetchData={fetchAnomalies}
                                filter={filter}
                                onError={setError}
                            />
                        </div>
                        <div className="chart-section">
                            <GraphComponent
                                logsChartData={[]}
                                pieData={[]}
                                alertChartData={[]}
                                anomaliesChartData={anomaliesChartData}
                                type="anomalies"
                            />
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default Dashboard;