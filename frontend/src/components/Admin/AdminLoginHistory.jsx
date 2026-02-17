import React, { useState, useEffect } from 'react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
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
        const doc = new jsPDF();
        const pageWidth = doc.internal.pageSize.width;

        // 1. Header with Background
        doc.setFillColor(30, 41, 59); // Dark blue header
        doc.rect(0, 0, pageWidth, 40, 'F');

        // 2. Logo / Branding
        doc.setFontSize(24);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(255, 255, 255);
        doc.text('QUICKFIX', 14, 22);

        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(200, 200, 200);
        doc.text('ARTIFICIAL INTELLIGENCE SOLUTIONS', 14, 30);

        // 3. Report Title & Date
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(255, 255, 255);
        doc.text('LOGIN AUDIT REPORT', pageWidth - 14, 22, { align: 'right' });

        doc.setFontSize(9);
        doc.setFont('helvetica', 'normal');
        doc.text(`Report Date: ${new Date().toLocaleString('en-IN')}`, pageWidth - 14, 30, { align: 'right' });

        // 4. Statistics Summary Grid
        if (stats) {
            doc.setFontSize(14);
            doc.setFont('helvetica', 'bold');
            doc.setTextColor(30, 41, 59);
            doc.text('SECURITY STATUS SUMMARY', 14, 55);

            // Draw a subtle border for stats
            doc.setDrawColor(226, 232, 240);
            doc.setLineWidth(0.3);
            doc.line(14, 58, pageWidth - 14, 58);

            // Stats Grid 
            // Total
            doc.setFontSize(10);
            doc.setTextColor(100, 116, 139);
            doc.text('TOTAL ATTEMPTS', 20, 70);
            doc.setFontSize(12);
            doc.setTextColor(30, 41, 59);
            doc.text(String(stats.total_logins), 20, 77);

            // Success
            doc.setFontSize(10);
            doc.setTextColor(100, 116, 139);
            doc.text('SUCCESSFUL', 70, 70);
            doc.setFontSize(12);
            doc.setTextColor(22, 163, 74); // Success green
            doc.text(String(stats.successful_logins), 70, 77);

            // Failed
            doc.setFontSize(10);
            doc.setTextColor(100, 116, 139);
            doc.text('FAILED', 120, 70);
            doc.setFontSize(12);
            doc.setTextColor(220, 38, 38); // Failed red
            doc.text(String(stats.failed_logins), 120, 77);

            // Rate
            doc.setFontSize(10);
            doc.setTextColor(100, 116, 139);
            doc.text('SUCCESS RATE', 165, 70);
            doc.setFontSize(12);
            doc.setTextColor(37, 99, 235); // Blue
            doc.text(`${stats.success_rate}%`, 165, 77);

            doc.line(14, 85, pageWidth - 14, 85);
        }

        // 5. Prepare High-Quality Table Data
        const tableColumn = ["ID", "EMAIL ADDRESS", "METHOD", "IP ORIGIN", "STATUS", "TIMESTAMP (IST)"];
        const tableRows = loginHistory.map(record => [
            record.id,
            record.email,
            record.login_method.toUpperCase(),
            record.ip_address || 'N/A',
            record.success ? '✓ SUCCESS' : '✗ FAILED',
            new Date(record.login_time).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' })
        ]);

        // 6. Professional Table Generation
        autoTable(doc, {
            head: [tableColumn],
            body: tableRows,
            startY: stats ? 95 : 55,
            theme: 'striped',
            headStyles: {
                fillColor: [30, 41, 59],
                textColor: [255, 255, 255],
                fontSize: 9,
                fontStyle: 'bold',
                halign: 'center',
                padding: 4
            },
            bodyStyles: {
                fontSize: 8,
                textColor: [51, 65, 85],
                cellPadding: 3
            },
            alternateRowStyles: {
                fillColor: [248, 250, 252]
            },
            columnStyles: {
                0: { halign: 'center', cellWidth: 10 },
                2: { halign: 'center', cellWidth: 25 },
                4: { halign: 'center', fontStyle: 'bold' }
            },
            didParseCell: (data) => {
                // Color status text
                if (data.section === 'body' && data.column.index === 4) {
                    if (data.cell.text[0].includes('SUCCESS')) {
                        data.cell.styles.textColor = [22, 163, 74];
                    } else if (data.cell.text[0].includes('FAILED')) {
                        data.cell.styles.textColor = [220, 38, 38];
                    }
                }
            },
            didDrawPage: (data) => {
                // 7. Premium Footer
                const str = `Page ${doc.internal.getNumberOfPages()}`;
                doc.setFontSize(8);
                doc.setFont('helvetica', 'italic');
                doc.setTextColor(148, 163, 184);

                // Footer divider
                doc.setDrawColor(226, 232, 240);
                doc.line(14, doc.internal.pageSize.height - 15, pageWidth - 14, doc.internal.pageSize.height - 15);

                doc.text(str, 14, doc.internal.pageSize.height - 10);
                doc.text('© 2026 Quickfix AI - Confidential Cloud Security Log', pageWidth - 14, doc.internal.pageSize.height - 10, { align: 'right' });
            }
        });

        // 8. Secure Direct Download
        doc.save(`quickfix-login-audit-${new Date().toISOString().split('T')[0]}.pdf`);
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
