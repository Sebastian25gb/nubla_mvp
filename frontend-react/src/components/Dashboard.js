import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import PaginatedTable from './PaginatedTable';
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
    const [filter, setFilter] = useState(''); // Estado para el filtrado

    useEffect(() => {
        const fetchTenants = async () => {
            try {
                const response = await axios.get('http://localhost:8000/tenants');
                setTenants(response.data.tenants || []);
                if (response.data.tenants && response.data.tenants.length > 0) {
                    setSelectedTenant(response.data.tenants[0].id);
                }
            } catch (error) {
                setError('Failed to load tenants');
            }
        };
        fetchTenants();
    }, []);

    const resetState = () => {
        setLogs([]);
        setThreats([]);
        setAlerts([]);
        setAnomalies([]);
        setLogsTotal(0);
        setThreatsTotal(0);
        setAlertsTotal(0);
        setAnomaliesTotal(0);
        setFilter(''); // Resetear el filtro
    };

    const fetchLogs = useCallback(async (from = 0, size = 50) => {
        if (!selectedTenant) return;
        try {
            const response = await axios.get(`http://localhost:8000/logs/${selectedTenant}`, {
                params: { from, size }
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
            setError(null);
        } catch (error) {
            setError('Failed to load logs');
        }
    }, [selectedTenant]);

    const fetchThreats = useCallback(async (from = 0, size = 50) => {
        if (!selectedTenant) return;
        try {
            const response = await axios.get(`http://localhost:8000/threats/${selectedTenant}`, {
                params: { from, size }
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
            setError(null);
        } catch (error) {
            setError('Failed to load threats');
        }
    }, [selectedTenant]);

    const fetchAlerts = useCallback(async (from = 0, size = 50) => {
        if (!selectedTenant) return;
        try {
            const response = await axios.get(`http://localhost:8000/alerts/${selectedTenant}`, {
                params: { from, size }
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
            setError(null);
        } catch (error) {
            setError('Failed to load alerts');
        }
    }, [selectedTenant]);

    const fetchAnomalies = useCallback(async (from = 0, size = 50) => {
        if (!selectedTenant) return;
        try {
            const response = await axios.get(`http://localhost:8000/anomalies/${selectedTenant}`, {
                params: { from, size }
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
            setError(null);
        } catch (error) {
            setError('Failed to load anomalies: ' + error.message);
        }
    }, [selectedTenant]);

    return (
        <div>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            <div className="controls">
                <select
                    value={selectedTenant}
                    onChange={(e) => { setSelectedTenant(e.target.value); resetState(); }}
                >
                    <option value="">Select Tenant</option>
                    {tenants.map(tenant => (
                        <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
                    ))}
                </select>
                <input
                    type="text"
                    placeholder="Filter logs..."
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                />
                <button onClick={() => { resetState(); fetchLogs(); }} disabled={!selectedTenant}>Load Logs</button>
                <button onClick={() => { resetState(); fetchThreats(); }} disabled={!selectedTenant}>Load Threats</button>
                <button onClick={() => { resetState(); fetchAlerts(); }} disabled={!selectedTenant}>Load Alerts</button>
                <button onClick={() => { resetState(); fetchAnomalies(); }} disabled={!selectedTenant}>Load Anomalies</button>
            </div>
            <PaginatedTable logs={logs} title="Logs" type="logs" total={logsTotal} fetchData={fetchLogs} filter={filter} />
            <PaginatedTable logs={threats} title="Threats" type="threats" total={threatsTotal} fetchData={fetchThreats} filter={filter} />
            <PaginatedTable logs={alerts} title="Alerts" type="alerts" total={alertsTotal} fetchData={fetchAlerts} filter={filter} />
            <PaginatedTable logs={anomalies} title="Anomalies" type="anomalies" total={anomaliesTotal} fetchData={fetchAnomalies} filter={filter} />
        </div>
    );
};

export default Dashboard;