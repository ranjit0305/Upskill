import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { companyAPI, assessmentAPI } from '../../services/api';
import {
    CheckCircle,
    AlertCircle,
    ArrowRight,
    BookOpen,
    Briefcase,
    Lightbulb,
    HelpCircle,
    BarChart,
    Search,
    Loader,
    Link as LinkIcon,
    Sparkles
} from 'lucide-react';
import './CompanyPrep.css';

const NOISY_INSIGHT_TERMS = [
    'intern offered',
    'have you placed',
    'suggest for preparation',
    'sites / books',
    'books you suggest',
    'general tips',
    'cleared the round',
    'question question',
    'your comments',
    'references',
    'and off on multiples',
];

const isHighQualityInsight = (text, { requireQuestion = false } = {}) => {
    if (!text) return false;

    const cleaned = String(text).replace(/\s+/g, ' ').trim();
    const lowered = cleaned.toLowerCase();
    const alphaOnly = lowered.replace(/[^a-z]/g, '');

    if (cleaned.length < (requireQuestion ? 12 : 16) || cleaned.length > 180) return false;
    if (NOISY_INSIGHT_TERMS.some((term) => lowered.includes(term))) return false;
    if (alphaOnly.length < (requireQuestion ? 8 : 12)) return false;
    if (requireQuestion && !cleaned.endsWith('?')) return false;
    if (!/[a-z]{3,}\s+[a-z]{3,}/i.test(cleaned)) return false;

    return true;
};

const getStrictInsightList = (items = [], options = {}) => {
    const seen = new Set();

    return items
        .map((item) => String(item || '').replace(/\s+/g, ' ').trim())
        .filter((item) => {
            if (!isHighQualityInsight(item, options)) return false;
            const key = item.toLowerCase();
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
};

const CompanyDashboard = () => {
    const { companyId } = useParams();
    const { user } = useAuth();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showTechnicalRound, setShowTechnicalRound] = useState(false);
    const [syncUrl, setSyncUrl] = useState('');
    const [syncLoading, setSyncLoading] = useState(false);
    const [syncMessage, setSyncMessage] = useState(null);

    useEffect(() => {
        const fetchDashboardData = async () => {
            setLoading(true);
            try {
                const response = await companyAPI.getDashboard(companyId, user.id);
                setData(response.data);
                setError(null);
            } catch (error) {
                console.error('Error fetching company dashboard:', error);
                setError(error.response?.data?.detail || 'Company not found or error loading data');
            } finally {
                setLoading(false);
            }
        };
        if (user && companyId) fetchDashboardData();
    }, [companyId, user]);

    const handleSyncOnline = async (e) => {
        e.preventDefault();
        if (!syncUrl) return;
        
        setSyncLoading(true);
        setSyncMessage(null);
        try {
            const response = await companyAPI.syncOnlineQuestions(companyId, [syncUrl]);
            setSyncMessage({ type: 'success', text: response.data.message });
            setSyncUrl('');
            // Refresh dashboard data to show new question count
            const dashboardRes = await companyAPI.getDashboard(companyId, user.id);
            setData(dashboardRes.data);
        } catch (error) {
            console.error('Error syncing online questions:', error);
            setSyncMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to sync from online source' });
        } finally {
            setSyncLoading(false);
            setTimeout(() => setSyncMessage(null), 5000);
        }
    };

    const handleAutoSync = async () => {
        setSyncLoading(true);
        setSyncMessage(null);
        try {
            const response = await companyAPI.autoSyncQuestions(companyId);
            setSyncMessage({ type: 'success', text: response.data.message });
            // Refresh dashboard data
            const dashboardRes = await companyAPI.getDashboard(companyId, user.id);
            setData(dashboardRes.data);
        } catch (error) {
            console.error('Error in auto-sync:', error);
            setSyncMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to auto-discover questions' });
        } finally {
            setSyncLoading(false);
            setTimeout(() => setSyncMessage(null), 5000);
        }
    };

    if (loading) return <div className="loading">Loading preparation dashboard...</div>;
    if (error || !data) return <div className="error">{error || 'Company not found'}</div>;

    const { company, insights, readiness_score, learning_path, company_profile, assessment_summary } = data;
    const faqs = getStrictInsightList(insights?.insights?.frequently_asked_questions || [], { requireQuestion: true });
    const commonMistakes = getStrictInsightList(insights?.insights?.common_mistakes || []);
    const breakdown = assessment_summary?.breakdown || {};
    const progress = assessment_summary?.progress || {};
    const scoreCards = [
        { key: 'aptitude', label: 'Aptitude' },
        { key: 'technical', label: 'Technical' },
        { key: 'coding', label: 'Coding' },
    ];

    return (
        <div className="company-dashboard-container container">
            <header className="dashboard-header">
                <div className="header-left">
                    <button className="btn-back" onClick={() => navigate('/companies')}>
                        <ArrowRight style={{ transform: 'rotate(180deg)' }} /> Back to Selection
                    </button>
                    <div className="title-row">
                        <h1>{company.name} Preparation Dashboard</h1>
                        {data.generated_questions && data.generated_questions.length > 0 && (
                            <span className="ai-badge pulse" onClick={() => document.getElementById('ai-questions-section')?.scrollIntoView({ behavior: 'smooth' })}>
                                {data.generated_questions.length} AI Questions Available
                            </span>
                        )}
                    </div>
                    <p className="dashboard-subtitle">
                        Company-specific readiness, interview insights, and assessment tracking in one place.
                    </p>
                </div>
                <div className="header-actions">
                        <button
                            className="btn btn-magic pulse header-action-btn"
                            onClick={handleAutoSync}
                            disabled={syncLoading}
                            title="Automatically find latest interview questions online"
                        >
                            {syncLoading ? <Loader className="spin" size={16} /> : <Sparkles size={16} />}
                            Auto-Discover
                        </button>
                        <button
                            className="btn btn-outline header-action-btn"
                            onClick={() => {
                                const url = prompt("Enter an interview experience URL (e.g., GeeksforGeeks):");
                                if (url) {
                                    setSyncUrl(url);
                                    // Trigger sync automatically for simplicity in this flow
                                    const triggerSync = async () => {
                                        setSyncLoading(true);
                                        try {
                                            const response = await companyAPI.syncOnlineQuestions(companyId, [url]);
                                            alert(response.data.message);
                                            const dashboardRes = await companyAPI.getDashboard(companyId, user.id);
                                            setData(dashboardRes.data);
                                        } catch (err) {
                                            alert("Failed to sync: " + (err.response?.data?.detail || err.message));
                                        } finally {
                                            setSyncLoading(false);
                                        }
                                    };
                                    triggerSync();
                                }
                            }}
                            disabled={syncLoading}
                        >
                            {syncLoading ? <Loader className="spin" size={16} /> : <Search size={16} />}
                            Manual Sync
                        </button>
                        <button
                            className="btn btn-secondary header-action-btn"
                            onClick={() => navigate(`/company/${companyId}/upload`)}
                        >
                            Upload Feedback
                        </button>
                </div>
            </header>

            {syncMessage && (
                <div className={`sync-banner ${syncMessage.type} fade-in`}>
                   {syncMessage.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                   {syncMessage.text}
                </div>
            )}

            <div className="company-profile-card card">
                <div className="section-title">
                    <Briefcase size={20} />
                    <h3>Extracted Company Details</h3>
                </div>
                <p className="company-profile-summary">
                    {company_profile?.summary || company.description || 'Upload interview feedback to build this company profile.'}
                </p>
                <div className="company-profile-metrics">
                    <div className="profile-metric">
                        <span className="metric-label">Feedback Files</span>
                        <span className="metric-value">{company_profile?.feedback_count || 0}</span>
                    </div>
                    <div className="profile-metric">
                        <span className="metric-label">Interview Rounds</span>
                        <span className="metric-value">{company_profile?.rounds_count || company_profile?.interview_rounds?.length || 0}</span>
                    </div>
                    <div className="profile-metric">
                        <span className="metric-label">Coding Difficulty</span>
                        <span className="metric-value">{company_profile?.coding_difficulty || 'unknown'}</span>
                    </div>
                </div>
                {company_profile?.focus_areas?.length > 0 && (
                    <div className="company-profile-group">
                        <h4>Focus Areas From Feedback</h4>
                        <div className="company-profile-tags">
                            {company_profile.focus_areas.map((area) => (
                                <span key={area} className="tag">{area}</span>
                            ))}
                        </div>
                    </div>
                )}
                {company_profile?.interview_rounds?.length > 0 && (
                    <div className="company-profile-group">
                        <h4>Detected Interview Rounds</h4>
                        <div className="company-profile-tags">
                            {company_profile.interview_rounds.map((round) => (
                                <span key={round} className="tag round-tag">{round}</span>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <div className="dashboard-grid">
                {/* Readiness Score Section */}
                <div className="dashboard-section readiness-section card">
                    <div className="section-title">
                        <BarChart size={20} />
                        <h3>{company.name} Readiness Score</h3>
                    </div>
                    <div className="readiness-display">
                        <div className="score-circle-small" style={{
                            borderColor: readiness_score >= 70 ? 'var(--success)' : readiness_score >= 40 ? 'var(--warning)' : 'var(--danger)'
                        }}>
                            <span className="value">{Math.round(readiness_score)}%</span>
                        </div>
                        <div className="readiness-info">
                            <p>This score is calculated from your cumulative aptitude, technical, and coding assessment performance for {company.name}.</p>
                            <span className={`status-badge ${readiness_score >= 70 ? 'high' : readiness_score >= 40 ? 'mid' : 'low'}`}>
                                {readiness_score >= 70 ? `Ready for ${company.name}` : readiness_score >= 40 ? 'Moderate Progress' : 'Needs Focus'}
                            </span>
                        </div>
                    </div>
                    <div className="score-breakdown-grid">
                        {scoreCards.map(({ key, label }) => {
                            const item = breakdown[key] || {};
                            const delta = item.delta;
                            const deltaClass = delta > 0 ? 'up' : delta < 0 ? 'down' : 'flat';

                            return (
                                <div key={key} className="score-breakdown-card">
                                    <div className="score-breakdown-header">
                                        <h4>{label}</h4>
                                        <span className="score-breakdown-value">{Math.round(item.average_score || 0)}%</span>
                                    </div>
                                    <p>Latest: {Math.round(item.latest_score || 0)}%</p>
                                    <p>Attempts: {item.attempts || 0}</p>
                                    <p className={`score-delta ${deltaClass}`}>
                                        {delta === null || delta === undefined
                                            ? 'No previous attempt yet'
                                            : delta > 0
                                                ? `+${Math.round(delta)}% from previous`
                                                : delta < 0
                                                    ? `${Math.round(delta)}% from previous`
                                                    : 'No change from previous'}
                                    </p>
                                </div>
                            );
                        })}
                    </div>
                </div>

                <div className="dashboard-section rounds-section card">
                    <div className="section-title">
                        <Briefcase size={20} />
                        <h3>Typical Interview Rounds</h3>
                    </div>
                    <div className="rounds-list-detailed">
                        {insights && insights.rounds_summary && insights.rounds_summary.length > 0 ? (
                            insights.rounds_summary.map((round, index) => (
                                <div key={index} className="round-item-detailed">
                                    <div className="round-badge">{index + 1}</div>
                                    <div className="round-content">
                                        <div className="round-header-row">
                                            <h3>{round.name || `Round ${index + 1}`}</h3>
                                            {(round.name.toLowerCase().includes('aptitude') || round.name.toLowerCase().includes('technical')) && (
                                                <button
                                                    className="btn-practice-mini"
                                                    onClick={() => document.getElementById('ai-questions-section')?.scrollIntoView({ behavior: 'smooth' })}
                                                >
                                                    Practice Questions
                                                </button>
                                            )}
                                        </div>
                                        <p>{round.description || 'No detailed description available.'}</p>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <p className="empty-msg">No interview rounds information available yet.</p>
                        )}
                    </div>
                </div>

                <div className="dashboard-section progress-section card">
                    <div className="section-title">
                        <BarChart size={20} />
                        <h3>Progress Comparison</h3>
                    </div>
                    <p className="progress-summary">
                        {progress.summary || 'Complete more company assessments to compare your latest scores against previous attempts.'}
                    </p>
                    <div className="progress-columns">
                        <div className="progress-group improved">
                            <h4>Where You Improved</h4>
                            {progress.improved_areas?.length > 0 ? (
                                <ul className="progress-list">
                                    {progress.improved_areas.map((item, index) => (
                                        <li key={`improved-${index}`}>{item}</li>
                                    ))}
                                </ul>
                            ) : (
                                <p className="empty-msg">No improvement trend available yet.</p>
                            )}
                        </div>
                        <div className="progress-group focus">
                            <h4>Where To Improve</h4>
                            {progress.focus_areas?.length > 0 ? (
                                <ul className="progress-list">
                                    {progress.focus_areas.map((item, index) => (
                                        <li key={`focus-${index}`}>{item}</li>
                                    ))}
                                </ul>
                            ) : (
                                <p className="empty-msg">No major weak area detected yet.</p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Learning Path */}
                <div className="dashboard-section path-section card">
                    <div className="section-title">
                        <BookOpen size={20} />
                        <h3>Personalized Learning Path</h3>
                    </div>
                    <div className="path-list">
                        {learning_path.map((item, index) => (
                            <div key={index} className={`path-item ${item.priority}`}>
                                <div className="path-header">
                                    <span className="topic">{item.topic}</span>
                                    <span className="priority-label">{item.priority.toUpperCase()}</span>
                                </div>
                                <p className="reason">{item.reason}</p>
                            </div>
                        ))}
                        {learning_path.length === 0 && <p className="empty-msg">Start taking assessments to see recommendations.</p>}
                    </div>
                </div>

                {/* Extracted Insights (FAQs, Tips, Mistakes) */}
                <div className="dashboard-section insights-section card">
                    <div className="section-title">
                        <Lightbulb size={20} />
                        <h3>Top Interview Insights</h3>
                    </div>

                    <div className="insight-tabs">
                        <div className="insight-group">
                            <h4><HelpCircle size={16} /> Frequently Asked Questions</h4>
                            {faqs.length > 0 ? (
                                <ul className="insight-list">
                                    {faqs.slice(0, 5).map((faq, i) => (
                                        <li key={i}>{faq}</li>
                                    ))}
                                </ul>
                            ) : (
                                <p className="empty-msg">No high-quality FAQ insights available from uploaded feedback yet.</p>
                            )}
                        </div>

                        <div className="insight-group">
                            <h4><AlertCircle size={16} /> Common Mistakes to Avoid</h4>
                            {commonMistakes.length > 0 ? (
                                <ul className="mistake-list">
                                    {commonMistakes.slice(0, 3).map((mistake, i) => (
                                        <li key={i}>{mistake}</li>
                                    ))}
                                </ul>
                            ) : (
                                <p className="empty-msg">No reliable mistake patterns were extracted from the current feedback set.</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            <div className="cta-section">
                <h3>Ready to test your {company.name} readiness?</h3>
                <p>Select a round to start a specialized mock test based on {company.name}'s patterns.</p>
                <div className="cta-buttons round-selection-grid">
                    <button
                        className="btn btn-primary btn-round"
                        onClick={async () => {
                            try {
                                setLoading(true);
                                const res = await assessmentAPI.getCompanyAptitudeTest(companyId);
                                navigate(`/assessments/${res.data.id}`);
                            } catch (err) {
                                console.error("Failed to start aptitude test", err);
                                alert("Failed to generate test. Make sure you have enough aptitude questions in the database.");
                            } finally {
                                setLoading(false);
                            }
                        }}
                    >
                        <div className="btn-content">
                            <span className="round-name">Aptitude Round</span>
                            <span className="round-meta">20 Questions • 60 Mins</span>
                        </div>
                    </button>

                    <button
                        className="btn btn-primary btn-round"
                        onClick={async () => {
                            try {
                                setLoading(true);
                                const res = await assessmentAPI.getCompanyCodingTest(companyId);
                                navigate(`/coding/${res.data.id}`);
                            } catch (err) {
                                console.error("Failed to start coding test", err);
                                alert("Failed to generate coding test. Make sure you have coding questions in the database.");
                            } finally {
                                setLoading(false);
                            }
                        }}
                    >
                        <div className="btn-content">
                            <span className="round-name">Coding Round</span>
                            <span className="round-meta">4 Problems • 80 Mins</span>
                        </div>
                    </button>

                    <button
                        className={`btn btn-round ${showTechnicalRound ? 'btn-primary' : 'btn-outline'}`}
                        onClick={() => {
                            setShowTechnicalRound(!showTechnicalRound);
                            if (!showTechnicalRound) {
                                setTimeout(() => {
                                    document.getElementById('technical-round-details')?.scrollIntoView({ behavior: 'smooth' });
                                }, 100);
                            }
                        }}
                    >
                        <div className="btn-content">
                            <span className="round-name">Technical Round</span>
                            <span className="round-meta">20 Questions • 40 Mins</span>
                        </div>
                    </button>

                    <button
                        className="btn btn-secondary btn-round"
                        onClick={() => navigate(`/company/${companyId}/mock-interview`)}
                    >
                        <div className="btn-content">
                            <span className="round-name">Mock Interview</span>
                            <span className="round-meta">HR • Technical • Coding Discussion</span>
                        </div>
                    </button>
                </div>
            </div>

            {showTechnicalRound && (
                <div id="technical-round-details" className="dashboard-section questions-section card full-width technical-round-overlay">
                    <div className="section-title">
                        <BookOpen size={20} />
                        <h3>Technical Round Preparation</h3>
                        <button className="btn-close-mini" onClick={() => setShowTechnicalRound(false)}>Close</button>
                    </div>

                    {/* Extracted Conceptual Questions */}
                    {insights?.insights.technical_questions && insights.insights.technical_questions.length > 0 && (
                        <div className="tech-questions-section-inner">
                            <h4 className="sub-section-title">Feedback-Based Conceptual Questions</h4>
                            <div className="tech-questions-grid">
                                {insights.insights.technical_questions.map((item, qIdx) => (
                                    <div key={qIdx} className="tech-q-card">
                                        <div className="tech-q-header">
                                            <span className="topic-tag">{item.topic}</span>
                                        </div>
                                        <p className="tech-q-text">{item.question}</p>
                                        <div className="referral-links">
                                            <span className="links-label">Study Materials:</span>
                                            <div className="links-list">
                                                {item.referral_links.map((link, lIdx) => (
                                                    <a
                                                        key={lIdx}
                                                        href={link.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="ref-link"
                                                    >
                                                        {link.label}
                                                    </a>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* AI Generated MCQs */}
                    <div className="generated-questions-section-inner" style={{ marginTop: '2rem' }}>
                        <h4 className="sub-section-title">Technical Practice MCQs</h4>
                        <div className="generated-questions-list">
                            {data.generated_questions && data.generated_questions.length > 0 ? (
                                data.generated_questions.map((q, idx) => (
                                    q.type === "technical" && (
                                        <div key={idx} className="generated-q-card">
                                            <p className="q-text"><strong>Q:</strong> {q.question}</p>
                                            <div className="q-meta">
                                                <span className={`difficulty ${q.difficulty}`}>{q.difficulty}</span>
                                                <span className="category">{q.category}</span>
                                            </div>
                                        </div>
                                    )
                                ))
                            ) : (
                                <p className="empty-msg">No technical practice questions available yet.</p>
                            )}
                        </div>
                    </div>

                    <div className="round-actions">
                        <button
                            className="btn btn-primary"
                            onClick={async () => {
                                try {
                                    setLoading(true);
                                    const res = await assessmentAPI.getCompanyTechnicalTest(companyId);
                                    navigate(`/assessments/${res.data.id}`);
                                } catch (err) {
                                    console.error("Failed to start technical test", err);
                                    alert("Failed to generate technical test. Make sure you have enough technical questions in the database.");
                                } finally {
                                    setLoading(false);
                                }
                            }}
                        >
                            Start Technical Assessment
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CompanyDashboard;
