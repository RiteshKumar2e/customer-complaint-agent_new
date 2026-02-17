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

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this login record?')) return;

        try {
            await api.delete(`/auth/admin/login-history/${id}`);
            // Refresh list and stats
            fetchLoginHistory();
            fetchLoginStats();
        } catch (error) {
            console.error('Error deleting login record:', error);
            alert('Failed to delete record');
        }
    };


    const downloadCSV = () => {
        const headers = ['User Name', 'Email', 'Method', 'IP Address', 'Device Type', 'Location', 'Status', 'Success', 'Login Time', 'Logout Time', 'Created At'];
        const csvData = loginHistory.map(record => [

            record.user_name || 'N/A',
            record.email,
            record.login_method,
            record.ip_address || 'N/A',
            record.device_type || 'N/A',
            record.login_location || 'N/A',
            record.status || 'N/A',
            record.success ? 'Yes' : 'No',
            new Date(record.login_time).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }),
            record.logout_time ? new Date(record.logout_time).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : 'Logged In',
            new Date(record.created_at || record.login_time).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })
        ]);

        const csv = [
            headers.join(','),
            ...csvData.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `quickfix-login-audit-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    const downloadPDF = () => {
        const doc = new jsPDF('landscape');
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
        doc.text('ADVANCED LOGIN AUDIT REPORT', pageWidth - 14, 22, { align: 'right' });

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
            doc.setFontSize(10);
            doc.setTextColor(100, 116, 139);
            doc.text('TOTAL ATTEMPTS', 20, 70);
            doc.setFontSize(12);
            doc.setTextColor(30, 41, 59);
            doc.text(String(stats.total_logins), 20, 77);

            doc.text('SUCCESSFUL', 80, 70);
            doc.setFontSize(12);
            doc.setTextColor(22, 163, 74);
            doc.text(String(stats.successful_logins), 80, 77);

            doc.setTextColor(100, 116, 139);
            doc.text('FAILED', 140, 70);
            doc.setFontSize(12);
            doc.setTextColor(220, 38, 38);
            doc.text(String(stats.failed_logins), 140, 77);

            doc.setTextColor(100, 116, 139);
            doc.text('SUCCESS RATE', 200, 70);
            doc.setFontSize(12);
            doc.setTextColor(37, 99, 235);
            doc.text(`${stats.success_rate}%`, 200, 77);

            doc.line(14, 85, pageWidth - 14, 85);
        }

        // 5. Prepare High-Quality Table Data
        const tableColumn = ["USER NAME", "EMAIL ADDRESS", "PHONE", "METHOD", "DEVICE", "LOCATION", "STATUS", "LOGIN TIME", "LOGOUT TIME"];
        const tableRows = loginHistory.map(record => [

            record.user_name || 'N/A',
            record.email,
            record.phone || 'N/A',
            record.login_method.toUpperCase(),
            record.device_type || 'Desktop',
            record.login_location || 'India',
            record.success ? 'SUCCESS' : 'FAILED',
            new Date(record.login_time).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'short', timeStyle: 'short' }),
            record.logout_time ? new Date(record.logout_time).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'short', timeStyle: 'short' }) : 'ACTIVE'
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
                fontSize: 8,
                fontStyle: 'bold',
                halign: 'center'
            },
            bodyStyles: {
                fontSize: 7,
                textColor: [51, 65, 85],
                cellPadding: 2
            },
            alternateRowStyles: {
                fillColor: [248, 250, 252]
            },
            columnStyles: {
                2: { halign: 'center', cellWidth: 20 },
                3: { halign: 'center', cellWidth: 20 },
                5: { halign: 'center', fontStyle: 'bold' }
            },
            didParseCell: (data) => {
                if (data.section === 'body' && data.column.index === 6) {
                    if (data.cell.text[0] === 'SUCCESS') data.cell.styles.textColor = [22, 163, 74];
                    else if (data.cell.text[0] === 'FAILED') data.cell.styles.textColor = [220, 38, 38];
                }
                if (data.section === 'body' && data.column.index === 8 && data.cell.text[0] === 'ACTIVE') {
                    data.cell.styles.textColor = [37, 99, 235];
                    data.cell.styles.fontStyle = 'bold';
                }
            },

            didDrawPage: (data) => {
                const str = `Page ${doc.internal.getNumberOfPages()}`;
                doc.setFontSize(8);
                doc.setFont('helvetica', 'italic');
                doc.setTextColor(148, 163, 184);
                doc.line(14, doc.internal.pageSize.height - 15, pageWidth - 14, doc.internal.pageSize.height - 15);
                doc.text(str, 14, doc.internal.pageSize.height - 10);
                doc.text('© 2026 Quickfix AI - Confidential Security Audit Log', pageWidth - 14, doc.internal.pageSize.height - 10, { align: 'right' });
            }
        });

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
                <h1>🔐 Advanced Login Audit</h1>
                <p>Track user sessions, devices, and security events</p>
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
                        placeholder="Search by email or name..."
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
                                <th>User</th>
                                <th>Contact No</th>
                                <th>Method</th>
                                <th>Device</th>
                                <th>Location</th>
                                <th>Status</th>
                                <th>Login Time</th>
                                <th>Logout Time</th>
                                <th>Actions</th>
                            </tr>

                        </thead>
                        <tbody>
                            {loginHistory.map((record) => (
                                <tr key={record.id} className={record.success ? '' : 'failed-row'}>

                                    <td>
                                        <div className="user-cell">
                                            <span className="user-name">{record.user_name || 'N/A'}</span>
                                            <span className="user-email">{record.email}</span>
                                        </div>
                                    </td>
                                    <td>
                                        <span className="phone-cell">{record.phone || 'N/A'}</span>
                                    </td>
                                    <td>
                                        <span className={`method-badge ${getMethodBadgeClass(record.login_method)}`}>
                                            {record.login_method.toUpperCase()}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="device-info">
                                            <span className="device-type">{record.device_type || 'Desktop'}</span>
                                            <span className="ip-addr">{record.ip_address || 'N/A'}</span>
                                        </div>
                                    </td>
                                    <td className="location-cell">{record.login_location || 'India'}</td>
                                    <td>
                                        <span className={`status-badge ${record.success ? 'success' : 'failed'}`}>
                                            {record.success ? 'SUCCESS' : 'FAILED'}
                                        </span>
                                        {record.failure_reason && <span className="fail-reason">{record.failure_reason}</span>}
                                    </td>
                                    <td className="time-cell">
                                        {new Date(record.login_time).toLocaleString('en-IN', {
                                            timeZone: 'Asia/Kolkata',
                                            dateStyle: 'short',
                                            timeStyle: 'short'
                                        })}
                                    </td>
                                    <td className="time-cell">
                                        {record.logout_time ? (
                                            new Date(record.logout_time).toLocaleString('en-IN', {
                                                timeZone: 'Asia/Kolkata',
                                                dateStyle: 'short',
                                                timeStyle: 'short'
                                            })
                                        ) : (
                                            <span className="active-session">Active Now</span>
                                        )}
                                    </td>
                                    <td>
                                        <button
                                            className="delete-btn"
                                            onClick={() => handleDelete(record.id)}
                                            title="Delete Record"
                                        >
                                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                <polyline points="3 6 5 6 21 6"></polyline>
                                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                                <line x1="10" y1="11" x2="10" y2="17"></line>
                                                <line x1="14" y1="11" x2="14" y2="17"></line>
                                            </svg>
                                        </button>
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
                    <h2>🚨 Recent Critical Security Events</h2>
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
