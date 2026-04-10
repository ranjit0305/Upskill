import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Award, BarChart3, RotateCcw } from 'lucide-react';
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

    if (loading) {
        return <div className="loading">Loading mock interview report...</div>;
    }

    if (!session) {
        return <div className="loading">Mock interview report not found.</div>;
    }

    const backTarget = session.company_id ? `/company/${session.company_id}/mock-interview` : '/mock-interview';
    const startAgainLabel = session.company_name ? `Start Another ${session.company_name} Mock Interview` : 'Start Another';

    return (
        <div className="mock-page">
            <div className="mock-shell">
                <button className="mock-back" onClick={() => navigate(backTarget)}>
                    <ArrowLeft size={18} /> Back to Mock Interviews
                </button>

                <div className="mock-hero">
                    <div>
                        <h1>{session.company_name || 'General'} Mock Interview Report</h1>
                        <p>{session.summary || 'Review your score breakdown, answer quality, and suggested improvement areas.'}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => navigate(backTarget)}>
                        <RotateCcw size={16} /> {startAgainLabel}
                    </button>
                </div>

                <div className="mock-report-grid">
                    <div className="mock-card">
                        <div className="mock-score-card">
                            <div className="mock-score-circle">{Math.round(session.overall_score || 0)}%</div>
                            <div>
                                <div className="mock-pill"><Award size={14} /> Overall Score</div>
                                <h2 style={{ marginTop: '0.85rem' }}>Interview Performance Summary</h2>
                                <p className="mock-empty">{session.summary}</p>
                            </div>
                        </div>

                        <div className="mock-breakdown">
                            <div className="mock-breakdown-card">
                                <p>HR</p>
                                <strong>{Math.round(session.section_scores?.hr || 0)}%</strong>
                            </div>
                            <div className="mock-breakdown-card">
                                <p>Technical</p>
                                <strong>{Math.round(session.section_scores?.technical || 0)}%</strong>
                            </div>
                            <div className="mock-breakdown-card">
                                <p>Coding Discussion</p>
                                <strong>{Math.round(session.section_scores?.coding || 0)}%</strong>
                            </div>
                        </div>
                    </div>

                    <div className="mock-card">
                        <h3><BarChart3 size={18} style={{ verticalAlign: 'middle', marginRight: '0.45rem' }} /> Recommendations</h3>
                        <ul className="mock-rec-list">
                            {(session.recommendations || []).map((item, index) => (
                                <li key={index}>{item}</li>
                            ))}
                        </ul>
                    </div>
                </div>

                <div className="mock-card" style={{ marginTop: '1.5rem' }}>
                    <h3>Progress Comparison</h3>
                    <p className="mock-empty" style={{ marginBottom: '1rem' }}>
                        {session.comparison_summary || 'Complete at least two sessions in the same context to compare your progress.'}
                    </p>
                    <div className="mock-feedback-grid">
                        <div className="mock-feedback-box good">
                            <h5>Where You Improved</h5>
                            <ul className="mock-feedback-list">
                                {(session.improved_areas?.length ? session.improved_areas : ['No clear improvement trend yet.']).map((item, index) => (
                                    <li key={`improved-${index}`}>{item}</li>
                                ))}
                            </ul>
                        </div>
                        <div className="mock-feedback-box focus">
                            <h5>Where To Improve</h5>
                            <ul className="mock-feedback-list">
                                {(session.focus_areas?.length ? session.focus_areas : ['No major focus area identified yet.']).map((item, index) => (
                                    <li key={`focus-${index}`}>{item}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>

                {session.company_name && (
                    <div className="mock-card" style={{ marginTop: '1.5rem' }}>
                        <h3>Company Context</h3>
                        <p className="mock-empty">
                            This report compares only your <strong>{session.company_name}</strong> mock interview attempts, so the
                            trend reflects company-specific progress rather than your general practice history.
                        </p>
                    </div>
                )}

                <div className="mock-card" style={{ marginTop: '1.5rem' }}>
                    <h3>Question-By-Question Review</h3>
                    {session.answers?.length > 0 ? (
                        <div className="mock-answer-review">
                            {session.answers.map((item) => (
                                <div key={`${item.question_index}-${item.answered_at}`} className="mock-review-item">
                                    <div className="mock-review-top">
                                        <div>
                                            <div className="mock-pill">{item.category.toUpperCase()}</div>
                                            <h4>{item.prompt}</h4>
                                        </div>
                                        <div className="mock-review-score">{Math.round(item.feedback.score)}%</div>
                                    </div>

                                    <div className="mock-answer-text">{item.answer}</div>

                                    <div className="mock-feedback-grid">
                                        <div className="mock-feedback-box good">
                                            <h5>What Went Well</h5>
                                            <ul className="mock-feedback-list">
                                                {(item.feedback.strengths || []).map((point, index) => (
                                                    <li key={index}>{point}</li>
                                                ))}
                                            </ul>
                                        </div>
                                        <div className="mock-feedback-box focus">
                                            <h5>What To Improve</h5>
                                            <ul className="mock-feedback-list">
                                                {(item.feedback.improvements || []).map((point, index) => (
                                                    <li key={index}>{point}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>

                                    <div className="mock-model-answer">
                                        <strong>Suggested Answer Direction:</strong> {item.feedback.suggested_answer}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="mock-empty">No answers were submitted in this mock interview session yet.</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MockInterviewReport;
