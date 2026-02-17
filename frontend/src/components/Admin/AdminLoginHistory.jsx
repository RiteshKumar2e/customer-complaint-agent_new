import React, { useState, useEffect } from 'react';
import api from '../../api';
import '../../styles/AdminLoginHistory.css';

export default function AdminLoginHistory() {
    const [loginHistory, setLoginHistory] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [filterEmail, setFilterEmail] = useState('');
    const [limit, setLimit] = useState(100);

    useEffect(() => {
        fetchLoginHistory();
        fetchLoginStats();
    }, [filterEmail, limit]);

    const fetchLoginHistory = async () => {
        try {
            setLoading(true);
            const params = new URLSearchParams();
            if (filterEmail) params.append('email', filterEmail);
            params.append('limit', limit);

            const response = await api.get(`/auth/admin/login-history?${params}`);
            setLoginHistory(response.data.records);
        } catch (error) {
            console.error('Error fetching login history:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchLoginStats = async () => {
        try {
            const response = await api.get('/auth/admin/login-stats');
            setStats(response.data);
        } catch (error) {
            console.error('Error fetching login stats:', error);
        }
    };

    const downloadCSV = () => {
        const headers = ['ID', 'Email', 'Method', 'IP Address', 'User Agent', 'Success', 'Failure Reason', 'Login Time'];
        const csvData = loginHistory.map(record => [
            record.id,
            record.email,
            record.login_method,
            record.ip_address || 'N/A',
            record.user_agent || 'N/A',
            record.success ? 'Yes' : 'No',
            record.failure_reason || 'N/A',
            new Date(record.login_time).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })
        ]);

        const csv = [
            headers.join(','),
            ...csvData.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `login-history-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    const downloadPDF = () => {
        // Create HTML content for PDF
        const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Login History Report</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          h1 { color: #1e293b; text-align: center; }
          .stats { margin: 20px 0; padding: 15px; background: #f1f5f9; border-radius: 8px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { border: 1px solid #cbd5e1; padding: 10px; text-align: left; font-size: 12px; }
          th { background: #1e293b; color: white; }
          tr:nth-child(even) { background: #f8fafc; }
          .success { color: #16a34a; font-weight: bold; }
          .failed { color: #dc2626; font-weight: bold; }
          .footer { margin-top: 30px; text-align: center; color: #64748b; font-size: 12px; }
        </style>
      </head>
      <body>
        <h1>Login History Report</h1>
        <div class="stats">
          <p><strong>Generated:</strong> ${new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}</p>
          ${stats ? `
            <p><strong>Total Logins:</strong> ${stats.total_logins}</p>
            <p><strong>Successful:</strong> ${stats.successful_logins} | <strong>Failed:</strong> ${stats.failed_logins}</p>
            <p><strong>Success Rate:</strong> ${stats.success_rate}%</p>
          ` : ''}
        </div>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Email</th>
              <th>Method</th>
              <th>IP Address</th>
              <th>Status</th>
              <th>Failure Reason</th>
              <th>Login Time</th>
            </tr>
          </thead>
          <tbody>
            ${loginHistory.map(record => `
              <tr>
                <td>${record.id}</td>
                <td>${record.email}</td>
                <td>${record.login_method.toUpperCase()}</td>
                <td>${record.ip_address || 'N/A'}</td>
                <td class="${record.success ? 'success' : 'failed'}">
                  ${record.success ? '✓ Success' : '✗ Failed'}
                </td>
                <td>${record.failure_reason || '-'}</td>
                <td>${new Date(record.login_time).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        <div class="footer">
          <p>Quickfix AI - Login History Report</p>
          <p>This is a system-generated report</p>
        </div>
      </body>
      </html>
    `;

        // Open print dialog
        const printWindow = window.open('', '_blank');
        printWindow.document.write(htmlContent);
        printWindow.document.close();
        printWindow.print();
    };

    const getMethodBadgeClass = (method) => {
        switch (method) {
            case 'password': return 'method-password';
            case 'otp': return 'method-otp';
            case 'google': return 'method-google';
            default: return 'method-default';
        }
    };

    return (
        <div className="admin-login-history">
            <div className="page-header">
                <h1>🔐 Login History</h1>
                <p>Monitor and analyze user login activity</p>
            </div>

            {/* Statistics Cards */}
            {stats && (
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-icon">📊</div>
                        <div className="stat-content">
                            <h3>{stats.total_logins}</h3>
                            <p>Total Logins</p>
                        </div>
                    </div>
                    <div className="stat-card success">
                        <div className="stat-icon">✅</div>
                        <div className="stat-content">
                            <h3>{stats.successful_logins}</h3>
                            <p>Successful</p>
                        </div>
                    </div>
                    <div className="stat-card failed">
                        <div className="stat-icon">⚠️</div>
                        <div className="stat-content">
                            <h3>{stats.failed_logins}</h3>
                            <p>Failed</p>
                        </div>
                    </div>
                    <div className="stat-card rate">
                        <div className="stat-icon">📈</div>
                        <div className="stat-content">
                            <h3>{stats.success_rate}%</h3>
                            <p>Success Rate</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Filters and Actions */}
            <div className="controls-bar">
                <div className="filters">
                    <input
                        type="email"
                        placeholder="Filter by email..."
                        value={filterEmail}
                        onChange={(e) => setFilterEmail(e.target.value)}
                        className="filter-input"
                    />
                    <select
                        value={limit}
                        onChange={(e) => setLimit(Number(e.target.value))}
                        className="filter-select"
                    >
                        <option value={50}>50 records</option>
                        <option value={100}>100 records</option>
                        <option value={200}>200 records</option>
                        <option value={500}>500 records</option>
                    </select>
                </div>
                <div className="actions">
                    <button onClick={downloadCSV} className="btn-download csv">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                        Download CSV
                    </button>
                    <button onClick={downloadPDF} className="btn-download pdf">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                            <polyline points="10 9 9 9 8 9"></polyline>
                        </svg>
                        Download PDF
                    </button>
                </div>
            </div>

            {/* Login History Table */}
            <div className="table-container">
                {loading ? (
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>Loading login history...</p>
                    </div>
                ) : loginHistory.length === 0 ? (
                    <div className="empty-state">
                        <p>No login records found</p>
                    </div>
                ) : (
                    <table className="login-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Email</th>
                                <th>Method</th>
                                <th>IP Address</th>
                                <th>User Agent</th>
                                <th>Status</th>
                                <th>Failure Reason</th>
                                <th>Login Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loginHistory.map((record) => (
                                <tr key={record.id} className={record.success ? '' : 'failed-row'}>
                                    <td>{record.id}</td>
                                    <td className="email-cell">{record.email}</td>
                                    <td>
                                        <span className={`method-badge ${getMethodBadgeClass(record.login_method)}`}>
                                            {record.login_method.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="ip-cell">{record.ip_address || 'N/A'}</td>
                                    <td className="agent-cell" title={record.user_agent}>
                                        {record.user_agent ? record.user_agent.substring(0, 30) + '...' : 'N/A'}
                                    </td>
                                    <td>
                                        <span className={`status-badge ${record.success ? 'success' : 'failed'}`}>
                                            {record.success ? '✓ Success' : '✗ Failed'}
                                        </span>
                                    </td>
                                    <td className="reason-cell">{record.failure_reason || '-'}</td>
                                    <td className="time-cell">
                                        {new Date(record.login_time).toLocaleString('en-IN', {
                                            timeZone: 'Asia/Kolkata',
                                            dateStyle: 'medium',
                                            timeStyle: 'short'
                                        })}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Recent Failed Attempts */}
            {stats && stats.recent_failures && stats.recent_failures.length > 0 && (
                <div className="recent-failures">
                    <h2>🚨 Recent Failed Login Attempts</h2>
                    <div className="failures-list">
                        {stats.recent_failures.map((failure, index) => (
                            <div key={index} className="failure-item">
                                <div className="failure-icon">⚠️</div>
                                <div className="failure-details">
                                    <p className="failure-email">{failure.email}</p>
                                    <p className="failure-reason">{failure.reason}</p>
                                </div>
                                <div className="failure-meta">
                                    <span className={`method-badge ${getMethodBadgeClass(failure.method)}`}>
                                        {failure.method.toUpperCase()}
                                    </span>
                                    <span className="failure-time">
                                        {new Date(failure.time).toLocaleString('en-IN', {
                                            timeZone: 'Asia/Kolkata',
                                            timeStyle: 'short'
                                        })}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
