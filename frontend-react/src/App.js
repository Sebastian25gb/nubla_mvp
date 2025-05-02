import React, { useState, useEffect } from 'react';
import { getTenants, getLogs, getStats } from './api';
import { Bar, Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend } from 'chart.js';
import { saveAs } from 'file-saver';

// Registrar componentes de Chart.js
ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

function App() {
  const [tenants, setTenants] = useState([]);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [sortField, setSortField] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');

  // Cargar datos iniciales
  useEffect(() => {
    fetchData();
  }, []);

  // Actualizar logs cuando cambian los filtros
  useEffect(() => {
    fetchLogs();
  }, [selectedTenant, statusFilter, actionFilter, sortField, sortOrder]);

  const fetchData = async () => {
    try {
      const tenantsData = await getTenants();
      setTenants(tenantsData);

      const statsData = await getStats();
      setStats(statsData);
    } catch (err) {
      console.error('Error fetching data:', err);
    }
  };

  const fetchLogs = async () => {
    try {
      const logsData = await getLogs(selectedTenant);
      let filteredLogs = logsData;

      // Filtrar por status
      if (statusFilter) {
        filteredLogs = filteredLogs.filter(log => log.status === statusFilter);
      }

      // Filtrar por acción
      if (actionFilter) {
        filteredLogs = filteredLogs.filter(log => log.action === actionFilter);
      }

      // Ordenar
      filteredLogs.sort((a, b) => {
        const aValue = a[sortField];
        const bValue = b[sortField];
        if (sortField === 'timestamp') {
          return sortOrder === 'asc' ? new Date(aValue) - new Date(bValue) : new Date(bValue) - new Date(aValue);
        }
        return sortOrder === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
      });

      setLogs(filteredLogs);
    } catch (err) {
      console.error('Error fetching logs:', err);
    }
  };

  // Exportar logs a CSV
  const exportToCSV = () => {
    const headers = ['ID,Timestamp,Tenant,User ID,Action,Status,Bytes'];
    const rows = logs.map(log => 
      `${log.id},${log.timestamp},${log.tenant},${log.user_id},${log.action},${log.status},${log.bytes}`
    );
    const csvContent = headers.concat(rows).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, 'logs.csv');
  };

  // Preparar datos para las gráficas
  const statsChartData = {
    labels: stats.map(stat => stat.tenant),
    datasets: [
      {
        label: 'Total Logs',
        data: stats.map(stat => stat.total_logs),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
      },
      {
        label: 'Success Logs',
        data: stats.map(stat => stat.success_logs),
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
      },
      {
        label: 'Failure Logs',
        data: stats.map(stat => stat.failure_logs),
        backgroundColor: 'rgba(255, 99, 132, 0.6)',
      },
    ],
  };

  // Agrupar logs por fecha para el gráfico de líneas
  const logsByDate = logs.reduce((acc, log) => {
    const date = log.timestamp.split('T')[0];
    acc[date] = (acc[date] || 0) + 1;
    return acc;
  }, {});
  const lineChartData = {
    labels: Object.keys(logsByDate),
    datasets: [
      {
        label: 'Logs per Day',
        data: Object.values(logsByDate),
        fill: false,
        borderColor: 'rgba(75, 192, 192, 1)',
        tension: 0.1,
      },
    ],
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Nubla MVP</h1>

      {/* Filtros y Botones */}
      <div style={{ marginBottom: '20px' }}>
        <h2>Filters</h2>
        <div>
          <label>Tenant: </label>
          <select onChange={(e) => setSelectedTenant(e.target.value || null)} value={selectedTenant || ''}>
            <option value="">All Tenants</option>
            {tenants.map(tenant => (
              <option key={tenant} value={tenant}>{tenant}</option>
            ))}
          </select>
        </div>
        <div>
          <label>Status: </label>
          <select onChange={(e) => setStatusFilter(e.target.value || '')} value={statusFilter}>
            <option value="">All Statuses</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
          </select>
        </div>
        <div>
          <label>Action: </label>
          <select onChange={(e) => setActionFilter(e.target.value || '')} value={actionFilter}>
            <option value="">All Actions</option>
            <option value="login">Login</option>
            <option value="logout">Logout</option>
            <option value="file_access">File Access</option>
            <option value="data_transfer">Data Transfer</option>
          </select>
        </div>
        <div style={{ marginTop: '10px' }}>
          <button onClick={fetchData}>Refresh Data</button>
          <button onClick={exportToCSV} style={{ marginLeft: '10px' }}>Export to CSV</button>
          <button onClick={() => { setStatusFilter(''); setActionFilter(''); setSelectedTenant(null); }} style={{ marginLeft: '10px' }}>
            Clear Filters
          </button>
        </div>
      </div>

      {/* Estadísticas */}
      <div style={{ marginBottom: '20px' }}>
        <h2>Stats</h2>
        <Bar data={statsChartData} options={{ responsive: true, plugins: { legend: { position: 'top' } } }} />
        <ul>
          {stats.map(stat => (
            <li key={stat.tenant}>
              {stat.tenant}: Total Logs: {stat.total_logs}, Success: {stat.success_logs}, Failure: {stat.failure_logs}
            </li>
          ))}
        </ul>
      </div>

      {/* Gráfico de Logs por Fecha */}
      <div style={{ marginBottom: '20px' }}>
        <h2>Logs per Day</h2>
        <Line data={lineChartData} options={{ responsive: true, plugins: { legend: { position: 'top' } } }} />
      </div>

      {/* Logs */}
      <div>
        <h2>Logs</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th onClick={() => { setSortField('id'); setSortOrder(sortField === 'id' && sortOrder === 'asc' ? 'desc' : 'asc'); }} style={{ cursor: 'pointer' }}>
                ID {sortField === 'id' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => { setSortField('timestamp'); setSortOrder(sortField === 'timestamp' && sortOrder === 'asc' ? 'desc' : 'asc'); }} style={{ cursor: 'pointer' }}>
                Timestamp {sortField === 'timestamp' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => { setSortField('tenant'); setSortOrder(sortField === 'tenant' && sortOrder === 'asc' ? 'desc' : 'asc'); }} style={{ cursor: 'pointer' }}>
                Tenant {sortField === 'tenant' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => { setSortField('user_id'); setSortOrder(sortField === 'user_id' && sortOrder === 'asc' ? 'desc' : 'asc'); }} style={{ cursor: 'pointer' }}>
                User ID {sortField === 'user_id' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => { setSortField('action'); setSortOrder(sortField === 'action' && sortOrder === 'asc' ? 'desc' : 'asc'); }} style={{ cursor: 'pointer' }}>
                Action {sortField === 'action' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => { setSortField('status'); setSortOrder(sortField === 'status' && sortOrder === 'asc' ? 'desc' : 'asc'); }} style={{ cursor: 'pointer' }}>
                Status {sortField === 'status' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => { setSortField('bytes'); setSortOrder(sortField === 'bytes' && sortOrder === 'asc' ? 'desc' : 'asc'); }} style={{ cursor: 'pointer' }}>
                Bytes {sortField === 'bytes' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
            </tr>
          </thead>
          <tbody>
            {logs.map(log => (
              <tr key={log.id}>
                <td>{log.id}</td>
                <td>{log.timestamp}</td>
                <td>{log.tenant}</td>
                <td>{log.user_id}</td>
                <td>{log.action}</td>
                <td>{log.status}</td>
                <td>{log.bytes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;