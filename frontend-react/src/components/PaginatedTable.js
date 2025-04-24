import React, { useState } from 'react';
import './LogViewer.css';

const PaginatedTable = ({ logs, title, type, total, fetchData, filter = '' }) => {
    const [page, setPage] = useState(1);
    const itemsPerPage = 50;

    // Asegurarnos de que logs sea un array y total sea un número
    const validLogs = Array.isArray(logs) ? logs : [];
    const validTotal = typeof total === 'number' ? total : 0;

    // Filtrar los logs según el valor de filter
    const filteredLogs = validLogs.filter(log => 
        log.message && typeof log.message === 'string' && log.message.toLowerCase().includes(filter.toLowerCase())
    );

    const paginatedLogs = filteredLogs.slice((page - 1) * itemsPerPage, page * itemsPerPage);

    const handlePrevious = () => {
        setPage(page => Math.max(1, page - 1));
    };

    const handleNext = () => {
        const from = page * itemsPerPage;
        if (from < validTotal && fetchData) {
            fetchData(from, itemsPerPage);
        }
        setPage(page => page + 1);
    };

    return (
        <div className={`log-viewer ${type}`}>
            <h2>{title}</h2>
            {filteredLogs.length > 0 ? (
                <>
                    <div className="table-container">
                        <table className={`log-table ${type}`}>
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Tenant</th>
                                    <th>Message</th>
                                    {type === 'anomalies' ? <th>Reason</th> : <th>Status</th>}
                                </tr>
                            </thead>
                            <tbody>
                                {paginatedLogs.map((log, index) => (
                                    <tr key={index} className={log.message && log.message.toLowerCase().includes("failed") && type === "logs" ? "threat-row" : ""}>
                                        <td>{log.timestamp && log.timestamp.length > 20 ? log.timestamp.substring(0, 20) + '...' : log.timestamp || 'N/A'}</td>
                                        <td>{log.tenant || 'N/A'}</td>
                                        <td>{log.message && log.message.length > 50 ? log.message.substring(0, 50) + '...' : log.message || 'N/A'}</td>
                                        {type === 'anomalies' ? (
                                            <td>{log.reason || 'N/A'}</td>
                                        ) : (
                                            <td>{log.status || 'N/A'}</td>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <div className="pagination">
                        <button onClick={handlePrevious} disabled={page === 1}>Previous</button>
                        <span> Page {page} of {Math.ceil(validTotal / itemsPerPage)} </span>
                        <button onClick={handleNext} disabled={page * itemsPerPage >= validTotal}>Next</button>
                    </div>
                </>
            ) : (
                <p>No {title.toLowerCase()} match the filter.</p>
            )}
        </div>
    );
};

export default PaginatedTable;