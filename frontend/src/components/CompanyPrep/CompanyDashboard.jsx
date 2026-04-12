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
import RoadmapTree from '../Visualization/RoadmapTree';
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
        <div className="company-dashboard-container premium-bg">
            <div className="container animate-fade-in">
                <header className="dashboard-header">
                    <div className="header-left">
                        <button className="mock-back" onClick={() => navigate('/companies')}>
                            <ArrowRight style={{ transform: 'rotate(180deg)' }} /> Back to Selection
                        </button>
                        <div className="title-row">
                            <h1 style={{ margin: 0 }}>{company.name} Prep</h1>
                            {data.generated_questions && data.generated_questions.length > 0 && (
                                <span className="ai-badge pulse" onClick={() => document.getElementById('ai-questions-section')?.scrollIntoView({ behavior: 'smooth' })}>
                                    <Sparkles size={14} style={{ marginRight: '0.5rem' }} />
                                    {data.generated_questions.length} AI Questions
                                </span>
                            )}
                        </div>
                        <p className="dashboard-subtitle">
                            Company-specific readiness, interview insights, and assessment tracking.
                        </p>
                    </div>
                    <div className="header-actions">
                        <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            <button
                                className="btn btn-primary"
                                style={{ width: '100%', justifyContent: 'center' }}
                                onClick={handleAutoSync}
                                disabled={syncLoading}
                            >
                                {syncLoading ? <Loader className="spin" size={16} /> : <Sparkles size={16} />}
                                Auto-Discover
                            </button>
                            <button
                                className="btn-back glass"
                                style={{ width: '100%', justifyContent: 'center', marginBottom: 0 }}
                                onClick={() => navigate(`/company/${companyId}/upload`)}
                            >
                                Upload Feedback
                            </button>
                        </div>
                    </div>
                </header>

                {syncMessage && (
                    <div className={`sync-banner ${syncMessage.type} glass-card`} style={{ padding: '1rem', marginBottom: '2rem', borderLeft: `4px solid var(--${syncMessage.type === 'success' ? 'success' : 'danger'})` }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            {syncMessage.type === 'success' ? <CheckCircle size={20} color="var(--success)" /> : <AlertCircle size={20} color="var(--danger)" />}
                            <span style={{ fontWeight: 600 }}>{syncMessage.text}</span>
                        </div>
                    </div>
                )}

                <div className="company-profile-card glass-card">
                    <div className="section-title">
                        <Briefcase size={20} color="var(--primary)" />
                        <h3>Extracted Company Details</h3>
                    </div>
                    <p className="company-profile-summary">
                        {company_profile?.summary || company.description || 'Upload interview feedback to build this company profile.'}
                    </p>
                    <div className="company-profile-metrics">
                        <div className="profile-metric">
                            <span className="metric-label">Feedback</span>
                            <span className="metric-value">{company_profile?.feedback_count || 0} Files</span>
                        </div>
                        <div className="profile-metric">
                            <span className="metric-label">Rounds</span>
                            <span className="metric-value">{company_profile?.rounds_count || company_profile?.interview_rounds?.length || 0} Stages</span>
                        </div>
                        <div className="profile-metric">
                            <span className="metric-label">Difficulty</span>
                            <span className="metric-value" style={{ color: company_profile?.coding_difficulty === 'Hard' ? 'var(--danger)' : 'var(--success)' }}>
                                {company_profile?.coding_difficulty || 'Unknown'}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="dashboard-grid">
                    {/* Readiness Score Section */}
                    <div className="dashboard-section glass-card">
                        <div className="section-title">
                            <BarChart size={20} color="var(--primary)" />
                            <h3>Target Readiness</h3>
                        </div>
                        <div className="readiness-display" style={{ marginBottom: '2rem' }}>
                            <div className="score-circle-small" style={{
                                borderColor: readiness_score >= 70 ? 'var(--success)' : readiness_score >= 40 ? 'var(--warning)' : 'var(--danger)'
                            }}>
                                {Math.round(readiness_score)}%
                            </div>
                            <div className="readiness-info">
                                <p>Comprehensive score based on your cumulative performance for {company.name}.</p>
                                <div className={`mock-status-badge ${readiness_score >= 70 ? 'completed' : 'active'}`}>
                                    {readiness_score >= 70 ? 'Ready to Apply' : 'In Preparation'}
                                </div>
                            </div>
                        </div>
                        <div className="score-breakdown-grid">
                            {scoreCards.map(({ key, label }) => {
                                const item = breakdown[key] || {};
                                return (
                                    <div key={key} className="score-breakdown-card">
                                        <div className="score-breakdown-header">
                                            <h4 style={{ fontSize: '0.85rem', color: 'var(--slate)' }}>{label}</h4>
                                            <span style={{ fontWeight: 800 }}>{Math.round(item.average_score || 0)}%</span>
                                        </div>
                                        <div className="topic-bar-container" style={{ height: '4px', marginTop: '4px' }}>
                                            <div className="topic-bar" style={{ width: `${item.average_score || 0}%`, background: 'var(--primary)' }}></div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    <div className="dashboard-section glass-card">
                        <div className="section-title">
                            <BookOpen size={20} color="var(--primary)" />
                            <h3>Interview Roadmap</h3>
                        </div>
                        <div className="roadmap-viewport" style={{ maxHeight: '600px', overflowY: 'auto', paddingRight: '1rem' }}>
                            <RoadmapTree 
                                stages={insights?.rounds_summary?.map((round, idx) => ({
                                    ...round,
                                    title: round.name,
                                    status: idx === 0 ? 'in-progress' : idx < (insights.rounds_summary.length / 2) ? 'completed' : 'upcoming',
                                    score: idx === 0 ? readiness_score : undefined
                                }))} 
                            />
                        </div>
                    </div>
                </div>

                {/* Technical Intelligence Section */}
                <div className="dashboard-section glass-card full-width" style={{ marginTop: '2rem' }}>
                    <div className="section-title">
                        <Lightbulb size={20} color="var(--primary)" />
                        <h3>Technical Intelligence</h3>
                    </div>
                    {insights?.insights?.technical_questions?.length > 0 ? (
                        <div className="tech-questions-grid">
                            {insights.insights.technical_questions.map((q, idx) => (
                                <div key={idx} className="tech-q-card">
                                    <div className="tech-q-header">
                                        <span className="topic-tag">{q.topic}</span>
                                    </div>
                                    <p className="tech-q-text">{q.question}</p>
                                    {q.referral_links?.length > 0 && (
                                        <div className="referral-links">
                                            <span className="links-label">Referral Intelligence:</span>
                                            <div className="links-list">
                                                {q.referral_links.map((link, lIdx) => (
                                                    <a key={lIdx} href={link.url} target="_blank" rel="noopener noreferrer" className="ref-link">
                                                        {link.title}
                                                    </a>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="empty-msg">No structured technical questions found in current intelligence data.</p>
                    )}
                </div>

                {faqs.length > 0 && (
                    <div className="dashboard-section glass-card full-width" style={{ marginTop: '2rem' }}>
                        <div className="section-title">
                            <HelpCircle size={20} color="var(--primary)" />
                            <h3>Community Intelligence (FAQ)</h3>
                        </div>
                        <div className="tech-questions-grid">
                            {faqs.map((faq, idx) => (
                                <div key={idx} className="tech-q-card" style={{ background: 'white' }}>
                                    <p className="tech-q-text" style={{ fontSize: '0.95rem' }}>{faq}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <div className="cta-section glass-card" style={{ marginTop: '2rem' }}>
                    <h3 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.5rem' }}>Start Round Simulation</h3>
                    <p style={{ color: 'var(--slate)' }}>Select a round to start a specialized mock test based on {company.name}'s patterns.</p>
                    <div className="round-selection-grid">
                        <button className="btn-round" onClick={async () => {
                            try {
                                setLoading(true);
                                const res = await assessmentAPI.getCompanyAptitudeTest(companyId);
                                navigate(`/assessments/${res.data.id}`);
                            } catch (err) { alert("Test generation failed."); } finally { setLoading(false); }
                        }}>
                            <div className="btn-content">
                                <span className="round-name">Aptitude</span>
                                <span className="round-meta">60 Mins • Critical Thinking</span>
                            </div>
                        </button>

                        <button className="btn-round" onClick={async () => {
                            try {
                                setLoading(true);
                                const res = await assessmentAPI.getCompanyCodingTest(companyId);
                                navigate(`/coding/${res.data.id}`);
                            } catch (err) { alert("Coding test failed."); } finally { setLoading(false); }
                        }}>
                            <div className="btn-content">
                                <span className="round-name">Coding Round</span>
                                <span className="round-meta">80 Mins • DSA Focus</span>
                            </div>
                        </button>

                        <button className="btn-round" onClick={async () => {
                            try {
                                setLoading(true);
                                const res = await assessmentAPI.getCompanyTechnicalTest(companyId);
                                navigate(`/assessments/${res.data.id}`);
                            } catch (err) { alert("Technical test failed."); } finally { setLoading(false); }
                        }}>
                            <div className="btn-content">
                                <span className="round-name">Technical Round</span>
                                <span className="round-meta">45 Mins • Core Subjects</span>
                            </div>
                        </button>

                        <button className="btn-round" onClick={() => navigate(`/company/${companyId}/mock-interview`)}>
                            <div className="btn-content">
                                <span className="round-name" style={{ color: 'var(--primary)' }}>AI Interview</span>
                                <span className="round-meta">Full Simulation • Gemini AI</span>
                            </div>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );

};

export default CompanyDashboard;
