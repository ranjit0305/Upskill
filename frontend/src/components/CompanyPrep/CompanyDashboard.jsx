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
    BarChart
} from 'lucide-react';
import './CompanyPrep.css';

const CompanyDashboard = () => {
    const { companyId } = useParams();
    const { user } = useAuth();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

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

    if (loading) return <div className="loading">Loading Zoho preparation dashboard...</div>;
    if (error || !data) return <div className="error">{error || 'Company not found'}</div>;

    const { company, insights, readiness_score, learning_path } = data;

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
                    <p>{company.description}</p>
                </div>
                {user?.role !== 'student' && (
                    <button
                        className="btn btn-secondary"
                        onClick={() => navigate(`/company/${companyId}/upload`)}
                    >
                        Upload Feedback
                    </button>
                )}
            </header>

            <div className="dashboard-grid">
                {/* Readiness Score Section */}
                <div className="dashboard-section readiness-section card">
                    <div className="section-title">
                        <BarChart size={20} />
                        <h3>Zoho Readiness Score</h3>
                    </div>
                    <div className="readiness-display">
                        <div className="score-circle-small" style={{
                            borderColor: readiness_score >= 70 ? 'var(--success)' : readiness_score >= 40 ? 'var(--warning)' : 'var(--danger)'
                        }}>
                            <span className="value">{Math.round(readiness_score)}%</span>
                        </div>
                        <div className="readiness-info">
                            <p>This score is calculated based on your performance in topics frequently asked at Zoho.</p>
                            <span className={`status-badge ${readiness_score >= 70 ? 'high' : readiness_score >= 40 ? 'mid' : 'low'}`}>
                                {readiness_score >= 70 ? 'Ready for Zoho' : readiness_score >= 40 ? 'Moderate Progress' : 'Needs Focus'}
                            </span>
                        </div>
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
                            <ul className="insight-list">
                                {insights?.insights.frequently_asked_questions.slice(0, 5).map((faq, i) => (
                                    <li key={i}>{faq}</li>
                                ))}
                            </ul>
                        </div>

                        <div className="insight-group">
                            <h4><AlertCircle size={16} /> Common Mistakes to Avoid</h4>
                            <ul className="mistake-list">
                                {insights?.insights.common_mistakes.slice(0, 3).map((mistake, i) => (
                                    <li key={i}>{mistake}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>

                {/* AI Generated Questions */}
                <div id="ai-questions-section" className="dashboard-section questions-section card full-width">
                    <div className="section-title">
                        <HelpCircle size={20} />
                        <h3>AI-Generated Practice Questions</h3>
                    </div>
                    <div className="generated-questions-list">
                        {data.generated_questions && data.generated_questions.length > 0 ? (
                            data.generated_questions.map((q, idx) => (
                                <div key={idx} className="generated-q-card">
                                    <p className="q-text"><strong>Q:</strong> {q.question}</p>
                                    <div className="q-meta">
                                        <span className={`difficulty ${q.difficulty}`}>{q.difficulty}</span>
                                        <span className="category">{q.category}</span>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <p className="empty-msg">Upload more feedback documents to generate adaptive practice questions.</p>
                        )}
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
                            <span className="round-meta">50 Questions • 60 Mins</span>
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
                            <span className="round-meta">5 Problems • 90 Mins</span>
                        </div>
                    </button>

                    <button className="btn btn-outline btn-round" onClick={() => navigate('/assessments')}>
                        <div className="btn-content">
                            <span className="round-name">Technical Round</span>
                            <span className="round-meta">20 Questions • 30 Mins</span>
                        </div>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CompanyDashboard;
