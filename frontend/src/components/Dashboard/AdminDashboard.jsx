import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminAPI } from '../../services/api';
import { Users, BookOpen, Layers, TrendingUp, BarChart2, PlusCircle, Settings } from 'lucide-react';
import '../Admin/Admin.css';

const AdminDashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await adminAPI.getStats();
                setStats(response.data);
            } catch (error) {
                console.error('Error fetching admin stats:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    if (loading) return <div className="loading">Loading admin dashboard...</div>;

    return (
        <div className="admin-container">
            <header className="management-header">
                <div>
                    <h1>Admin Dashboard</h1>
                    <p>Manage platform content and view system analytics</p>
                </div>
                <div className="nav-right">
                    <button className="btn btn-outline" onClick={() => navigate('/dashboard')}>
                        Switch to Student View
                    </button>
                </div>
            </header>

            <div className="admin-grid">
                {/* Users Stat */}
                <div className="admin-card stat-card">
                    <div className="stat-icon" style={{ backgroundColor: '#e0e7ff' }}>
                        <Users size={24} color="#4338ca" />
                    </div>
                    <div className="stat-content">
                        <div className="stat-value">{stats?.users?.total || 0}</div>
                        <div className="stat-label">Total Users</div>
                        <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.5rem' }}>
                            {stats?.users?.students} Students | {stats?.users?.seniors} Seniors
                        </div>
                    </div>
                </div>

                {/* Content Stat */}
                <div className="admin-card stat-card">
                    <div className="stat-icon" style={{ backgroundColor: '#fef3c7' }}>
                        <BookOpen size={24} color="#d97706" />
                    </div>
                    <div className="stat-content">
                        <div className="stat-value">{stats?.content?.questions || 0}</div>
                        <div className="stat-label">Questions Pool</div>
                        <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.5rem' }}>
                            Across {stats?.content?.assessments} Assessments
                        </div>
                    </div>
                </div>

                {/* Performance Stat */}
                <div className="admin-card stat-card">
                    <div className="stat-icon" style={{ backgroundColor: '#d1fae5' }}>
                        <TrendingUp size={24} color="#059669" />
                    </div>
                    <div className="stat-content">
                        <div className="stat-value">{stats?.performance?.avg_readiness || 0}%</div>
                        <div className="stat-label">Avg Readiness Score</div>
                        <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.5rem' }}>
                            Based on {stats?.content?.submissions} submissions
                        </div>
                    </div>
                </div>
            </div>

            <h2 style={{ marginTop: '3rem', marginBottom: '1.5rem' }}>Quick Actions</h2>
            <div className="admin-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
                <div className="admin-card action-card" onClick={() => navigate('/admin/questions')}>
                    <PlusCircle size={32} color="var(--primary)" style={{ marginBottom: '1rem' }} />
                    <h3>Manage Questions</h3>
                    <p>Add, edit, or remove questions from the global pool.</p>
                </div>

                <div className="admin-card action-card" onClick={() => navigate('/admin/assessments')}>
                    <Layers size={32} color="var(--primary)" style={{ marginBottom: '1rem' }} />
                    <h3>Manage Assessments</h3>
                    <p>Create new tests by bundling questions together.</p>
                </div>

                <div className="admin-card action-card">
                    <BarChart2 size={32} color="var(--primary)" style={{ marginBottom: '1rem' }} />
                    <h3>Detailed Analytics</h3>
                    <p>View performance breakdown by category and batch.</p>
                </div>

                <div className="admin-card action-card">
                    <Settings size={32} color="var(--primary)" style={{ marginBottom: '1rem' }} />
                    <h3>System Settings</h3>
                    <p>Configure LLM parameters and platform constants.</p>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
