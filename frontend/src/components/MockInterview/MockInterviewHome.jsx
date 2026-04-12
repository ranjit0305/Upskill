import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
    ArrowLeft, 
    Briefcase, 
    MessageSquareText, 
    PlayCircle, 
    History, 
    TrendingUp, 
    Hash, 
    Calendar,
    ChevronRight,
    Target
} from 'lucide-react';
import { companyAPI, mockInterviewAPI } from '../../services/api';
import './MockInterview.css';

const QUESTION_OPTIONS = [3, 6, 9];

const MockInterviewHome = () => {
    const navigate = useNavigate();
    const { companyId } = useParams();
    const [company, setCompany] = useState(null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [starting, setStarting] = useState(false);
    const [questionCount, setQuestionCount] = useState(6);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const requests = [mockInterviewAPI.getHistory({ limit: 8, ...(companyId ? { company_id: companyId } : {}) })];
                if (companyId) {
                    requests.push(companyAPI.getDashboard(companyId));
                }
                const responses = await Promise.allSettled(requests);
                const historyResponse = responses[0];
                if (historyResponse.status === 'fulfilled') {
                    setHistory(historyResponse.value.data.sessions || []);
                }

                if (companyId && responses[1]?.status === 'fulfilled') {
                    setCompany(responses[1].value.data.company);
                }
            } catch (error) {
                console.error('Error loading mock interview home:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [companyId]);

    const stats = useMemo(() => {
        const completed = history.filter(s => s.status === 'completed');
        const totalSessions = completed.length;
        const avgScore = totalSessions > 0
            ? Math.round(completed.reduce((sum, s) => sum + (s.overall_score || 0), 0) / totalSessions)
            : 0;
        const lastDate = completed.length > 0 ? completed[0].started_at : null;
        return { totalSessions, avgScore, lastDate };
    }, [history]);

    const formatDate = (isoString) => {
        if (!isoString) return '—';
        const d = new Date(isoString);
        return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    };

    const scoreBadgeClass = (score) => {
        if (score >= 75) return 'green';
        if (score >= 55) return 'amber';
        return 'red';
    };

    const startInterview = async (mode) => {
        try {
            setStarting(true);
            const payload = {
                mode,
                question_count: questionCount,
            };
            if (mode === 'company') {
                payload.company_id = companyId;
            }
            const response = await mockInterviewAPI.startSession(payload);
            navigate(`/mock-interview/session/${response.data.id}`);
        } catch (error) {
            console.error('Error starting mock interview:', error);
            alert(error.response?.data?.detail || 'Failed to start mock interview');
        } finally {
            setStarting(false);
        }
    };

    return (
        <div className="mock-page premium-bg">
            <div className="mock-shell">
                <button className="mock-back glass" onClick={() => navigate(companyId ? `/company/${companyId}` : '/dashboard')}>
                    <ArrowLeft size={18} /> Back
                </button>

                <header className="mock-hero">
                    <div className="mock-hero-content">
                        <div className="ai-badge">AI-Powered Practice</div>
                        <h1>{companyId ? `${company?.name || 'Company'} Mock Interview` : 'Master Your Interviews'}</h1>
                        <p>
                            {companyId
                                ? `Prepare for ${company?.name || 'company'} specific rounds with tailored questions and real-time AI feedback.`
                                : 'Practice HR, technical, and coding discussion rounds with immersive voice interaction and deep analytics.'}
                        </p>
                    </div>
                </header>

                <div className="mock-stats-strip">
                    <div className="mock-stat-item glass-card">
                        <span className="mock-stat-label">Total Sessions</span>
                        <span className="mock-stat-value">{stats.totalSessions}</span>
                        <span className="mock-stat-sub">Completed practice</span>
                    </div>
                    <div className="mock-stat-item glass-card">
                        <span className="mock-stat-label">Average Score</span>
                        <span className="mock-stat-value">{stats.avgScore}%</span>
                        <span className="mock-stat-sub">Performance trend</span>
                    </div>
                    <div className="mock-stat-item glass-card">
                        <span className="mock-stat-label">Recent Activity</span>
                        <span className="mock-stat-value" style={{ fontSize: '1.25rem' }}>{formatDate(stats.lastDate)}</span>
                        <span className="mock-stat-sub">Last attempt</span>
                    </div>
                </div>

                <div className="mock-grid">
                    <section className="mock-card glass-card">
                        <div className="mock-card-header">
                            <Target className="text-indigo" size={24} />
                            <h2>Configure Your Session</h2>
                        </div>
                        <p className="mock-desc">Select the number of questions and the mode to begin your practice session.</p>

                        <div className="mock-count-picker">
                            <span className="mock-count-label">Question Count</span>
                            <div className="mock-count-group">
                                {QUESTION_OPTIONS.map(n => (
                                    <button
                                        key={n}
                                        className={`mock-count-btn ${questionCount === n ? 'active' : ''}`}
                                        onClick={() => setQuestionCount(n)}
                                    >
                                        {n}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="mock-mode-grid">
                            <div className="mock-mode-card">
                                <span className="mock-mode-badge"><MessageSquareText size={13} /> General</span>
                                <h3>General Interview</h3>
                                <p>Diverse questions covering core CS fundamentals, HR, and coding approach.</p>
                                <button className="btn btn-primary" disabled={starting} onClick={() => startInterview('general')}>
                                    {starting ? 'Initializing...' : 'Start Session'} <ChevronRight size={16} />
                                </button>
                            </div>

                            <div className={`mock-mode-card ${!companyId ? 'disabled' : ''}`}>
                                <span className="mock-mode-badge company"><Briefcase size={13} /> Company</span>
                                <h3>{companyId ? company?.name : 'Company Mode'}</h3>
                                <p>Role-specific questions based on real feedback from {companyId ? company?.name : 'companies'}.</p>
                                <button
                                    className="btn btn-glass"
                                    disabled={starting || !companyId}
                                    onClick={() => startInterview('company')}
                                >
                                    {starting ? 'Initializing...' : 'Start Session'} <ChevronRight size={16} />
                                </button>
                            </div>
                        </div>
                    </section>

                    <aside className="mock-card glass-card">
                        <div className="mock-card-header">
                            <History className="text-slate" size={20} />
                            <h3>Recent Performance</h3>
                        </div>
                        {loading ? (
                            <div className="mock-loading-shimmer">Loading history...</div>
                        ) : history.length > 0 ? (
                            <div className="mock-list">
                                {history.map((item) => (
                                    <div key={item.id} className="mock-history-item" onClick={() => navigate(`/mock-interview/session/${item.id}/report`)} style={{ cursor: 'pointer' }}>
                                        <div className="mock-history-top">
                                            <h4>{item.company_name || 'General Practice'}</h4>
                                            <span className={`mock-score-badge ${scoreBadgeClass(item.overall_score || 0)}`}>
                                                {Math.round(item.overall_score || 0)}%
                                            </span>
                                        </div>
                                        <div className="mock-history-meta">
                                            <span>{item.mode.toUpperCase()}</span>
                                            <span className="dot">•</span>
                                            <span>{item.answered_questions} / {item.total_questions} Qs</span>
                                            <span className="dot">•</span>
                                            <span>{formatDate(item.started_at)}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="mock-empty-state">
                                <History size={48} strokeWidth={1} />
                                <p>No sessions found. Start your first practice to see analytics.</p>
                            </div>
                        )}
                    </aside>
                </div>
            </div>
        </div>
    );
};

export default MockInterviewHome;

