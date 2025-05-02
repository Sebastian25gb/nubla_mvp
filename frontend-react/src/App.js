import React, { useState, useEffect } from 'react';
import { getTenants, getLogs, getStats } from './api';
import './App.css'; // Importamos los estilos

function App() {
  const [tenants, setTenants] = useState([]);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState(null);

  useEffect(() => {
    // Obtener la lista de tenants
    getTenants().then(data => setTenants(data)).catch(err => console.error(err));

    // Obtener estadísticas
    getStats().then(data => setStats(data)).catch(err => console.error(err));
  }, []);

  useEffect(() => {
    // Obtener logs, filtrados por tenant si se selecciona uno
    getLogs(selectedTenant).then(data => setLogs(data)).catch(err => console.error(err));
  }, [selectedTenant]);

  return (
    <div>
      <h1>Nubla MVP</h1>

      {/* Lista de Tenants */}
      <div>
        <h2>Tenants</h2>
        <select onChange={(e) => setSelectedTenant(e.target.value || null)} value={selectedTenant || ''}>
          <option value="">All Tenants</option>
          {tenants.map(tenant => (
            <option key={tenant} value={tenant}>{tenant}</option>
          ))}
        </select>
      </div>

      {/* Estadísticas */}
      <div>
        <h2>Stats</h2>
        <ul>
          {stats.map(stat => (
            <li key={stat.tenant}>
              {stat.tenant}: Total Logs: {stat.total_logs}, Success: {stat.success_logs}, Failure: {stat.failure_logs}
            </li>
          ))}
        </ul>
      </div>

      {/* Logs */}
      <div>
        <h2>Logs</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Timestamp</th>
              <th>Tenant</th>
              <th>User ID</th>
              <th>Action</th>
              <th>Status</th>
              <th>Bytes</th>
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