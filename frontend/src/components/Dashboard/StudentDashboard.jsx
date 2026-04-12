import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { performanceAPI } from '../../services/api';
import { 
    RadarChart, 
    PolarGrid, 
    PolarAngleAxis, 
    PolarRadiusAxis, 
    Radar, 
    ResponsiveContainer,
    Tooltip
} from 'recharts';
import { TrendingUp, Award, Target, BookOpen, LogOut, ChevronRight, Layout } from 'lucide-react';
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
        if (score >= 80) return '#10b981';
        if (score >= 60) return '#f59e0b';
        return '#ef4444';
    };

    const radarData = useMemo(() => {
        if (!readiness) return [];
        return [
            { subject: 'Aptitude', score: readiness.component_scores.aptitude },
            { subject: 'Technical', score: readiness.component_scores.technical },
            { subject: 'Coding', score: readiness.component_scores.coding },
            { subject: 'Consistency', score: readiness.component_scores.consistency },
        ];
    }, [readiness]);

    if (loading) {
        return <div className="loading">Preparing your career landscape...</div>;
    }

    return (
        <div className="dashboard premium-bg">
            <nav className="navbar">
                <div className="container nav-content">
                    <div className="nav-left">
                        <h2 style={{ color: '#1e1b4b', fontWeight: 900, fontSize: '1.5rem' }}>Upskill</h2>
                    </div>
                    <div className="nav-right">
                        {(user?.role === 'admin' || user?.role === 'senior') && (
                            <button onClick={() => navigate('/admin')} className="btn btn-outline">
                                <Layout size={16} /> Admin Panel
                            </button>
                        )}
                        <span style={{ fontWeight: 600, color: '#475569' }}>{user?.profile?.name}</span>
                        <button onClick={logout} className="btn-back" style={{ color: '#ef4444', background: 'rgba(239, 68, 68, 0.05)' }}>
                            <LogOut size={16} /> Logout
                        </button>
                    </div>
                </div>
            </nav>

            <div className="container dashboard-content animate-fade-in">
                <div className="dashboard-header">
                    <h1>Your Placement Journey</h1>
                    <p>Track your growth across technical and behavioral dimensions.</p>
                </div>

                {/* Readiness Score Card */}
                <div className="score-card">
                    <div className="score-main">
                        <div className="score-circle">
                            <div className="score-value">{Math.round(readiness?.overall_score || 0)}</div>
                            <div className="score-label">Readiness</div>
                        </div>
                        <div className="score-info">
                            <h3>Overall Placement Readiness</h3>
                            <p>{readiness?.explanation || "Track your progress to see detailed insights about your readiness."}</p>
                            <div className={`mock-status-badge ${readiness?.overall_score >= 80 ? 'completed' : 'active'}`}>
                                {readiness?.overall_score >= 80 ? 'Battle Ready' : 'In Preparation'}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="stats-grid">
                    <div className="stat-card glass-card">
                        <div className="stat-icon" style={{ backgroundColor: 'rgba(99, 102, 241, 0.1)' }}>
                            <Target size={24} color="#6366f1" />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{performance?.metrics?.total_attempts || 0}</div>
                            <div className="stat-label">Tests Taken</div>
                        </div>
                    </div>

                    <div className="stat-card glass-card">
                        <div className="stat-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                            <Award size={24} color="#10b981" />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{Math.round(performance?.metrics?.accuracy || 0)}%</div>
                            <div className="stat-label">Avg Accuracy</div>
                        </div>
                    </div>

                    <div className="stat-card glass-card">
                        <div className="stat-icon" style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)' }}>
                            <TrendingUp size={24} color="#f59e0b" />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{Math.round(performance?.metrics?.consistency_score || 0)}%</div>
                            <div className="stat-label">Consistency</div>
                        </div>
                    </div>

                    <div className="stat-card glass-card">
                        <div className="stat-icon" style={{ backgroundColor: 'rgba(139, 92, 246, 0.1)' }}>
                            <BookOpen size={24} color="#8b5cf6" />
                        </div>
                        <div className="stat-content">
                            <div className="stat-value">{performance?.metrics?.avg_speed?.toFixed(1) || 0}</div>
                            <div className="stat-label">Ques/Min</div>
                        </div>
                    </div>
                </div>

                {/* Charts */}
                <div className="charts-grid">
                    <div className="glass-card">
                        <h3>Domain Mastery</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <RadarChart data={radarData}>
                                <PolarGrid stroke="rgba(203, 213, 225, 0.5)" />
                                <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }} />
                                <Radar name="Score" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} />
                                <Tooltip />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="glass-card recommendations-card">
                        <h3>AI Recommendations</h3>
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

                {/* Topic-wise Mastery */}
                <div className="glass-card topic-mastery-card">
                    <h3>Technical Topic Breakdown</h3>
                    <div className="topic-grid">
                        {performance?.topic_performance?.map((tp, index) => (
                            <div key={index} className="topic-metric">
                                <div className="topic-info-row">
                                    <span className="topic-name">{tp?.topic?.toUpperCase() || 'UNKNOWN'}</span>
                                    <span className="topic-percentage">{Math.round(tp?.accuracy || 0)}%</span>
                                </div>
                                <div className="topic-bar-container">
                                    <div 
                                        className="topic-bar" 
                                        style={{ 
                                            width: `${tp?.accuracy || 0}%`,
                                            backgroundColor: getScoreColor(tp?.accuracy || 0)
                                        }}
                                    ></div>
                                </div>
                                <div className="topic-stats">
                                    <span>{tp?.correct_answers || 0} Correct</span>
                                    <span>Last Activity: {tp?.updated_at ? new Date(tp.updated_at).toLocaleDateString() : 'N/A'}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="action-buttons">
                    <button className="btn btn-primary" onClick={() => navigate('/assessments')}>
                        Practice Tests <ChevronRight size={16} />
                    </button>
                    <button className="btn btn-secondary" style={{ background: '#4f46e5' }} onClick={() => navigate('/companies')}>
                        Company Prep
                    </button>
                    <button className="btn-back glass" onClick={() => navigate('/mock-interview')}>
                        AI Mock Interview
                    </button>
                </div>
            </div>
        </div>
    );
};

export default StudentDashboard;

