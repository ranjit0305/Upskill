import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
    ArrowLeft, 
    Award, 
    BarChart3, 
    RotateCcw, 
    CheckCircle2, 
    AlertCircle, 
    TrendingUp,
    Zap,
    Target
} from 'lucide-react';
import { 
    Radar, 
    RadarChart, 
    PolarGrid, 
    PolarAngleAxis, 
    ResponsiveContainer 
} from 'recharts';
import { mockInterviewAPI } from '../../services/api';
import './MockInterview.css';

const MockInterviewReport = () => {
    const { sessionId } = useParams();
    const navigate = useNavigate();
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSession = async () => {
            try {
                const response = await mockInterviewAPI.getSession(sessionId);
                setSession(response.data);
            } catch (error) {
                console.error('Error fetching mock interview report:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchSession();
    }, [sessionId]);

    const radarData = useMemo(() => {
        if (!session || !session.section_scores) return [];
        const overall = session.overall_score || 0;
        const hr = session.section_scores.hr || 0;
        const tech = session.section_scores.technical || 0;
        const coding = session.section_scores.coding || 0;

        return [
            { subject: 'Relevance', A: overall > 70 ? 85 : Math.max(overall, 40), fullMark: 100 },
            { subject: 'Clarity', A: hr || 60, fullMark: 100 },
            { subject: 'Structure', A: tech || 55, fullMark: 100 },
            { subject: 'Confidence', A: Math.max(overall - 5, 50), fullMark: 100 },
            { subject: 'Technical', A: tech || 50, fullMark: 100 },
            { subject: 'Coding', A: coding || 40, fullMark: 100 },
        ];
    }, [session]);

    if (loading) {
        return <div className="loading">Generating your performance analysis...</div>;
    }

    if (!session) {
        return <div className="loading">Mock interview report not found.</div>;
    }

    const backTarget = session.company_id ? `/company/${session.company_id}/mock-interview` : '/mock-interview';
    const startAgainLabel = session.company_name ? `Retry ${session.company_name}` : 'Practice Again';

    return (
        <div className="mock-page">
            <div className="mock-shell">
                <button className="mock-back" onClick={() => navigate(backTarget)}>
                    <ArrowLeft size={18} /> Exit Report
                </button>

                <div className="mock-hero">
                    <div className="mock-hero-content">
                        <div className="mock-badge">Performance Scorecard</div>
                        <h1>{session.company_name || 'General'} Session Report</h1>
                        <p>{session.summary || 'Review your AI-generated insights and improvement roadmap.'}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => navigate(backTarget)}>
                        <RotateCcw size={16} /> {startAgainLabel}
                    </button>
                </div>

                <div className="mock-report-grid">
                    <div className="mock-card main-stats">
                        <div className="mock-score-header">
                            <div className="mock-score-visual">
                                <div className="mock-score-value">{Math.round(session.overall_score || 0)}<span>%</span></div>
                                <div className="mock-score-label">Overall Readiness</div>
                            </div>
                            <div className="mock-radar-container">
                                <ResponsiveContainer width="100%" height={240}>
                                    <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                                        <PolarGrid stroke="rgba(99, 102, 241, 0.1)" />
                                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 11, fontWeight: 600 }} />
                                        <Radar
                                            name="Score"
                                            dataKey="A"
                                            stroke="#6366f1"
                                            fill="#6366f1"
                                            fillOpacity={0.2}
                                        />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        <div className="mock-metric-grid">
                            <div className="mock-metric-card">
                                <span className="label">HR Rounds</span>
                                <div className="value-row">
                                    <div className="bar"><div className="fill hr" style={{ width: `${session.section_scores?.hr || 0}%` }}></div></div>
                                    <span className="num">{Math.round(session.section_scores?.hr || 0)}%</span>
                                </div>
                            </div>
                            <div className="mock-metric-card">
                                <span className="label">Technical</span>
                                <div className="value-row">
                                    <div className="bar"><div className="fill technical" style={{ width: `${session.section_scores?.technical || 0}%` }}></div></div>
                                    <span className="num">{Math.round(session.section_scores?.technical || 0)}%</span>
                                </div>
                            </div>
                            <div className="mock-metric-card">
                                <span className="label">Coding Discussion</span>
                                <div className="value-row">
                                    <div className="bar"><div className="fill coding" style={{ width: `${session.section_scores?.coding || 0}%` }}></div></div>
                                    <span className="num">{Math.round(session.section_scores?.coding || 0)}%</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="mock-report-sidebar">
                        <div className="mock-card glass sidebar-card">
                            <div className="card-title">
                                <Zap className="text-amber" size={18} />
                                <h3>AI Recommendations</h3>
                            </div>
                            <ul className="mock-rec-list">
                                {(session.recommendations || []).map((item, index) => (
                                    <li key={index}>
                                        <CheckCircle2 size={14} className="text-indigo" />
                                        {item}
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <div className="mock-card glass sidebar-card">
                            <div className="card-title">
                                <TrendingUp className="text-indigo" size={18} />
                                <h3>Progress Insights</h3>
                            </div>
                            <p className="mock-insight-text">{session.comparison_summary}</p>
                            <div className="mock-trends">
                                <div className="trend-item plus">
                                    <CheckCircle2 size={14} />
                                    <span>{session.improved_areas?.[0] || 'Baseline session started.'}</span>
                                </div>
                                <div className="trend-item minus">
                                    <AlertCircle size={14} />
                                    <span>{session.focus_areas?.[0] || 'Keep practicing for trending data.'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="mock-section-title">
                    <Target size={20} />
                    <h2>Deep Analysis by Question</h2>
                </div>

                <div className="mock-answer-review">
                    {session.answers?.length > 0 ? (
                        session.answers.map((item, idx) => (
                            <div key={idx} className="mock-review-item glass">
                                <div className="mock-review-header">
                                    <div className="header-main">
                                        <span className={`category-pill ${item.category}`}>{item.category.toUpperCase()}</span>
                                        <h4>{item.prompt}</h4>
                                    </div>
                                    <div className="score-badge-large">{Math.round(item.feedback.score)}%</div>
                                </div>

                                <div className="mock-user-answer">
                                    <label>Your Response</label>
                                    <p>{item.answer}</p>
                                </div>

                                <div className="mock-feedback-columns">
                                    <div className="feedback-group strengths">
                                        <h5>Key Strengths</h5>
                                        <ul>
                                            {(item.feedback.strengths || []).map((point, k) => <li key={k}>{point}</li>)}
                                        </ul>
                                    </div>
                                    <div className="feedback-group gaps">
                                        <h5>Knowledge Gaps</h5>
                                        <ul>
                                            {(item.feedback.improvements || []).map((point, k) => <li key={k}>{point}</li>)}
                                        </ul>
                                    </div>
                                </div>

                                <div className="mock-model-direction">
                                    <div className="direction-accent">Interviewer Guide</div>
                                    <p><strong>Ideal Focus:</strong> {item.feedback.suggested_answer}</p>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="mock-card empty-state">No questions were attempted in this session.</div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MockInterviewReport;

