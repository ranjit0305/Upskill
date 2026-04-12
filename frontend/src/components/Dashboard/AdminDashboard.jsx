import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminAPI } from '../../services/api';
import { Users, BookOpen, Layers, TrendingUp, BarChart2, PlusCircle, Settings, Layout } from 'lucide-react';
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
        <div className="admin-container premium-bg">
            <div className="container animate-fade-in">
                <header className="management-header">
                    <div>
                        <h1>Executive Control</h1>
                        <p style={{ color: 'var(--slate)', fontSize: '1.1rem' }}>Orchestrating platform intelligence and user growth.</p>
                    </div>
                    <div className="nav-right">
                        <button className="btn-back glass" onClick={() => navigate('/dashboard')}>
                            <Layout size={16} /> Switch to Student View
                        </button>
                    </div>
                </header>

                <div className="admin-grid">
                    {/* Users Stat */}
                    <div className="admin-card stat-card">
                        <div className="stat-icon" style={{ backgroundColor: 'rgba(99, 102, 241, 0.1)' }}>
                            <Users size={28} color="#6366f1" />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{stats?.users?.total || 0}</div>
                            <div className="stat-label">Total Talent</div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--slate)', marginTop: '0.75rem', fontWeight: 600 }}>
                                {stats?.users?.students} Students • {stats?.users?.seniors} Mentors
                            </div>
                        </div>
                    </div>

                    {/* Content Stat */}
                    <div className="admin-card stat-card">
                        <div className="stat-icon" style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)' }}>
                            <BookOpen size={28} color="#f59e0b" />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{stats?.content?.questions || 0}</div>
                            <div className="stat-label">Intelligence Pool</div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--slate)', marginTop: '0.75rem', fontWeight: 600 }}>
                                Across {stats?.content?.assessments} Active Assessments
                            </div>
                        </div>
                    </div>

                    {/* Performance Stat */}
                    <div className="admin-card stat-card">
                        <div className="stat-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                            <TrendingUp size={28} color="#10b981" />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{stats?.performance?.avg_readiness || 0}%</div>
                            <div className="stat-label">Avg Platform Readiness</div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--slate)', marginTop: '0.75rem', fontWeight: 600 }}>
                                From {stats?.content?.submissions} Global Submissions
                            </div>
                        </div>
                    </div>
                </div>

                <h2 style={{ marginTop: '4rem', marginBottom: '2rem', fontWeight: 900, letterSpacing: '-0.02em' }}>Platform Governance</h2>
                <div className="admin-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
                    <div className="admin-card action-card" onClick={() => navigate('/admin/questions')}>
                        <div style={{ marginBottom: '1.5rem', background: '#eef2ff', padding: '1rem', borderRadius: '16px', display: 'inline-flex' }}>
                            <PlusCircle size={32} color="var(--primary)" />
                        </div>
                        <h3>Question Library</h3>
                        <p style={{ color: 'var(--slate)', fontSize: '0.9rem' }}>Curate the global knowledge base with technical and behavioral questions.</p>
                    </div>

                    <div className="admin-card action-card" onClick={() => navigate('/admin/assessments')}>
                        <div style={{ marginBottom: '1.5rem', background: '#eef2ff', padding: '1rem', borderRadius: '16px', display: 'inline-flex' }}>
                            <Layers size={32} color="var(--primary)" />
                        </div>
                        <h3>Assessment Architect</h3>
                        <p style={{ color: 'var(--slate)', fontSize: '0.9rem' }}>Design immersive testing experiences by clustering domain questions.</p>
                    </div>

                    <div className="admin-card action-card">
                        <div style={{ marginBottom: '1.5rem', background: '#eef2ff', padding: '1rem', borderRadius: '16px', display: 'inline-flex' }}>
                            <BarChart2 size={32} color="var(--primary)" />
                        </div>
                        <h3>Talent Analytics</h3>
                        <p style={{ color: 'var(--slate)', fontSize: '0.9rem' }}>Deep dive into batch-wise performance and mastery trends.</p>
                    </div>

                    <div className="admin-card action-card" onClick={() => navigate('/admin/settings')}>
                        <div style={{ marginBottom: '1.5rem', background: '#eef2ff', padding: '1rem', borderRadius: '16px', display: 'inline-flex' }}>
                            <Settings size={32} color="var(--primary)" />
                        </div>
                        <h3>Enterprise Config</h3>
                        <p style={{ color: 'var(--slate)', fontSize: '0.9rem' }}>Fine-tune LLM parameters, prompt weights, and system logic.</p>
                    </div>
                </div>
            </div>
        </div>
    );

};

export default AdminDashboard;
