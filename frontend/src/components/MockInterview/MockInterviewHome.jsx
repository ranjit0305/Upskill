import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Briefcase, MessageSquareText, PlayCircle, History } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { companyAPI, mockInterviewAPI } from '../../services/api';
import './MockInterview.css';

const MockInterviewHome = () => {
    const navigate = useNavigate();
    const { companyId } = useParams();
    const { user } = useAuth();
    const [company, setCompany] = useState(null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [starting, setStarting] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const requests = [mockInterviewAPI.getHistory({ limit: 8, ...(companyId ? { company_id: companyId } : {}) })];
                if (companyId && user?.id) {
                    requests.push(companyAPI.getDashboard(companyId, user.id));
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
        if (user) {
            fetchData();
        }
    }, [companyId, user]);

    const startInterview = async (mode) => {
        try {
            setStarting(true);
            const payload = {
                mode,
                question_count: 6,
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
        <div className="mock-page">
            <div className="mock-shell">
                <button className="mock-back" onClick={() => navigate(companyId ? `/company/${companyId}` : '/dashboard')}>
                    <ArrowLeft size={18} /> Back
                </button>

                <div className="mock-hero">
                    <div>
                        <h1>{companyId ? `${company?.name || 'Company'} Mock Interview` : 'Mock Interview Practice'}</h1>
                        <p>
                            {companyId
                                ? `Practice HR, technical, and coding discussion rounds using ${company?.name || 'company'} feedback patterns, extracted topics, and company-aware evaluation.`
                                : 'Practice HR, technical, and coding discussion rounds in one guided session and get instant feedback on structure, relevance, and improvement areas.'}
                        </p>
                    </div>
                </div>

                <div className="mock-grid">
                    <div className="mock-card">
                        <h2>Start A Session</h2>
                        <p className="mock-empty">
                            {companyId
                                ? 'This company-specific mock interview uses uploaded interview topics and company patterns wherever available.'
                                : 'Choose the mock interview type you want to practice right now.'}
                        </p>

                        <div className="mock-mode-grid">
                            <div className="mock-mode-card">
                                <span className="mock-mode-badge"><MessageSquareText size={14} /> General</span>
                                <h3>General Mock Interview</h3>
                                <p>Practice placement-focused HR, technical, and coding discussion questions.</p>
                                <button className="btn btn-primary" disabled={starting} onClick={() => startInterview('general')}>
                                    <PlayCircle size={16} /> Start General
                                </button>
                            </div>

                            <div className="mock-mode-card">
                                <span className="mock-mode-badge"><Briefcase size={14} /> Company</span>
                                <h3>{companyId ? `${company?.name || 'Company'} Mock Interview` : 'Company-Specific'}</h3>
                                <p>
                                    {companyId
                                        ? 'Practice with company-aligned prompts derived from uploaded feedback and extracted topics.'
                                        : 'Start this from a company dashboard to get a company-specific mock interview.'}
                                </p>
                                <button
                                    className="btn btn-secondary"
                                    disabled={starting || !companyId}
                                    onClick={() => startInterview('company')}
                                >
                                    <PlayCircle size={16} /> Start Company
                                </button>
                            </div>
                        </div>
                    </div>

                    <div className="mock-card">
                        <h3><History size={18} style={{ verticalAlign: 'middle', marginRight: '0.45rem' }} /> Recent Sessions</h3>
                        {loading ? (
                            <p className="mock-empty">Loading history...</p>
                        ) : history.length > 0 ? (
                            <div className="mock-list">
                                {history.map((item) => (
                                    <div key={item.id} className="mock-history-item">
                                        <h4>{item.company_name || 'General Mock Interview'}</h4>
                                        <div className="mock-history-meta">
                                            <span>{item.mode.toUpperCase()}</span>
                                            <span>{Math.round(item.overall_score || 0)}%</span>
                                            <span>{item.answered_questions}/{item.total_questions} answered</span>
                                        </div>
                                        <button
                                            className="btn btn-outline"
                                            style={{ marginTop: '0.9rem' }}
                                            onClick={() => navigate(`/mock-interview/session/${item.id}/report`)}
                                        >
                                            View Report
                                        </button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="mock-empty">
                                {companyId
                                    ? `No ${company?.name || 'company'} mock interview sessions yet. Start your first session to build company-specific practice history.`
                                    : 'No mock interview sessions yet. Start your first session to build practice history.'}
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MockInterviewHome;
