import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { performanceAPI } from '../../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { TrendingUp, Award, Target, BookOpen } from 'lucide-react';
import './Dashboard.css';

const StudentDashboard = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [readiness, setReadiness] = useState(null);
    const [performance, setPerformance] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [readinessRes, performanceRes] = await Promise.all([
                performanceAPI.getReadinessScore(),
                performanceAPI.getPerformance()
            ]);
            setReadiness(readinessRes.data);
            setPerformance(performanceRes.data);
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            setLoading(false);
        }
    };

    const getScoreColor = (score) => {
        if (score >= 80) return 'var(--success)';
        if (score >= 60) return 'var(--warning)';
        return 'var(--danger)';
    };

    const getScoreBadge = (score) => {
        if (score >= 80) return 'badge-success';
        if (score >= 60) return 'badge-warning';
        return 'badge-danger';
    };

    if (loading) {
        return <div className="loading">Loading your dashboard...</div>;
    }

    const radarData = readiness ? [
        { subject: 'Aptitude', score: readiness.component_scores.aptitude },
        { subject: 'Technical', score: readiness.component_scores.technical },
        { subject: 'Coding', score: readiness.component_scores.coding },
        { subject: 'Consistency', score: readiness.component_scores.consistency },
    ] : [];

    return (
        <div className="dashboard">
            <nav className="navbar">
                <div className="container nav-content">
                    <h2>Upskill</h2>
                    <div className="nav-right">
                        {(user?.role === 'admin' || user?.role === 'senior') && (
                            <button onClick={() => navigate('/admin')} className="btn btn-secondary" style={{ marginRight: '1rem' }}>
                                Admin Dashboard
                            </button>
                        )}
                        <span>Welcome, {user?.profile?.name}</span>
                        <button onClick={logout} className="btn btn-outline">Logout</button>
                    </div>
                </div>
            </nav>

            <div className="container dashboard-content">
                <div className="dashboard-header">
                    <h1>Your Placement Dashboard</h1>
                    <p>Track your progress and improve your readiness</p>
                </div>

                {/* Readiness Score Card */}
                <div className="score-card">
                    <div className="score-main">
                        <div className="score-circle" style={{ borderColor: getScoreColor(readiness?.overall_score || 0) }}>
                            <div className="score-value">{Math.round(readiness?.overall_score || 0)}</div>
                            <div className="score-label">Readiness Score</div>
                        </div>
                        <div className="score-info">
                            <h3>Placement Readiness</h3>
                            <p>{readiness?.explanation}</p>
                            <span className={`badge ${getScoreBadge(readiness?.overall_score || 0)}`}>
                                {readiness?.overall_score >= 80 ? 'Excellent' : readiness?.overall_score >= 60 ? 'Good' : 'Needs Improvement'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-icon" style={{ backgroundColor: '#e0e7ff' }}>
                            <Target size={24} color="var(--primary)" />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{performance?.metrics?.total_attempts || 0}</div>
                            <div className="stat-label">Tests Taken</div>
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-icon" style={{ backgroundColor: '#d1fae5' }}>
                            <Award size={24} color="var(--success)" />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{Math.round(performance?.metrics?.accuracy || 0)}%</div>
                            <div className="stat-label">Avg Accuracy</div>
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-icon" style={{ backgroundColor: '#fef3c7' }}>
                            <TrendingUp size={24} color="var(--warning)" />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{Math.round(performance?.metrics?.consistency_score || 0)}%</div>
                            <div className="stat-label">Consistency</div>
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-icon" style={{ backgroundColor: '#e0e7ff' }}>
                            <BookOpen size={24} color="var(--secondary)" />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{performance?.metrics?.avg_speed?.toFixed(1) || 0}</div>
                            <div className="stat-label">Ques/Min</div>
                        </div>
                    </div>
                </div>

                {/* Charts */}
                <div className="charts-grid">
                    <div className="card chart-card">
                        <h3>Component Breakdown</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <RadarChart data={radarData}>
                                <PolarGrid />
                                <PolarAngleAxis dataKey="subject" />
                                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                                <Radar name="Score" dataKey="score" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.6} />
                                <Tooltip />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="card recommendations-card">
                        <h3>Personalized Recommendations</h3>
                        <div className="recommendations-list">
                            {readiness?.recommendations?.map((rec, index) => (
                                <div key={index} className="recommendation-item">
                                    <div className="rec-number">{index + 1}</div>
                                    <p>{rec}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="action-buttons">
                    <button className="btn btn-primary" onClick={() => navigate('/assessments')}>
                        Take Assessment
                    </button>
                    <button className="btn btn-secondary" style={{ backgroundColor: '#4f46e5', color: 'white' }} onClick={() => navigate('/companies')}>
                        Company-Wise Preparation
                    </button>
                    <button className="btn btn-outline" onClick={() => navigate('/practice')}>
                        Practice Questions
                    </button>
                </div>
            </div>
        </div>
    );
};

export default StudentDashboard;
