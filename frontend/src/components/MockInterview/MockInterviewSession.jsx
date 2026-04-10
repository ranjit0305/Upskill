import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, MessageSquareText, Timer } from 'lucide-react';
import { mockInterviewAPI } from '../../services/api';
import './MockInterview.css';

const MockInterviewSession = () => {
    const { sessionId } = useParams();
    const navigate = useNavigate();
    const [session, setSession] = useState(null);
    const [answer, setAnswer] = useState('');
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        const fetchSession = async () => {
            try {
                const response = await mockInterviewAPI.getSession(sessionId);
                setSession(response.data);
                if (response.data.status === 'completed') {
                    navigate(`/mock-interview/session/${sessionId}/report`, { replace: true });
                }
            } catch (error) {
                console.error('Error fetching mock interview session:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchSession();
    }, [navigate, sessionId]);

    const progressPercent = useMemo(() => {
        if (!session?.total_questions) return 0;
        return (session.current_question_index / session.total_questions) * 100;
    }, [session]);

    const backTarget = session?.company_id ? `/company/${session.company_id}/mock-interview` : '/mock-interview';

    const handleSubmit = async () => {
        if (!answer.trim()) {
            alert('Please enter your answer before continuing.');
            return;
        }

        try {
            setSubmitting(true);
            const response = await mockInterviewAPI.submitAnswer(sessionId, { answer });
            setAnswer('');
            if (response.data.completed) {
                navigate(`/mock-interview/session/${sessionId}/report`);
                return;
            }
            setSession(response.data.session);
        } catch (error) {
            console.error('Error submitting mock interview answer:', error);
            alert(error.response?.data?.detail || 'Failed to submit answer');
        } finally {
            setSubmitting(false);
        }
    };

    const handleFinish = async () => {
        if (!window.confirm('Finish this mock interview now? You can still review the report after ending it.')) {
            return;
        }

        try {
            setSubmitting(true);
            await mockInterviewAPI.finishSession(sessionId);
            navigate(`/mock-interview/session/${sessionId}/report`);
        } catch (error) {
            console.error('Error finishing mock interview:', error);
            alert(error.response?.data?.detail || 'Failed to finish mock interview');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return <div className="loading">Loading mock interview session...</div>;
    }

    if (!session?.current_question) {
        return <div className="loading">This mock interview session is unavailable.</div>;
    }

    const question = session.current_question;

    return (
        <div className="mock-page">
            <div className="mock-shell mock-session-shell">
                <button className="mock-back" onClick={() => navigate(backTarget)}>
                    <ArrowLeft size={18} /> Back to Mock Interview
                </button>

                <div className="mock-card">
                    <div className="mock-session-header">
                        <div>
                            <div className="mock-pill"><MessageSquareText size={14} /> {session.company_name || 'General'} Mock Interview</div>
                            <h1 style={{ marginTop: '0.9rem' }}>Question {question.index + 1} of {session.total_questions}</h1>
                            <p className="mock-empty">
                                {session.company_name
                                    ? `Answer like you're in a ${session.company_name} interview: stay structured, specific, and company-aware.`
                                    : 'Answer naturally, but keep your response structured and specific.'}
                            </p>
                        </div>
                        <div className="mock-pill"><Timer size={14} /> Live Session</div>
                    </div>

                    <div className="mock-progress-bar">
                        <div className="mock-progress-fill" style={{ width: `${progressPercent}%` }} />
                    </div>

                    <div className="mock-question-card">
                        <div className="mock-question-meta">
                            <span>{question.category.toUpperCase()}</span>
                            {question.topic && <span>{question.topic}</span>}
                            <span>{question.difficulty}</span>
                            <span>{question.source.replace('_', ' ')}</span>
                        </div>
                        <h2>{question.prompt}</h2>

                        <textarea
                            className="mock-answer-box"
                            placeholder="Type your interview answer here. Try to explain clearly, include examples, and show your thought process."
                            value={answer}
                            onChange={(e) => setAnswer(e.target.value)}
                        />

                        <div className="mock-actions">
                            <button className="btn btn-outline" onClick={handleFinish} disabled={submitting}>
                                Finish Now
                            </button>
                            <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
                                <CheckCircle2 size={16} />
                                {submitting ? 'Submitting...' : 'Submit Answer'}
                            </button>
                        </div>
                    </div>
                </div>

                <div className="mock-tips">
                    <div className="mock-tip-card">
                        <h4>How To Answer Better</h4>
                        <p className="mock-empty">Use a simple flow: context, approach, example, and result. Avoid vague or one-line answers.</p>
                    </div>
                    <div className="mock-tip-card">
                        <h4>What The Evaluator Looks For</h4>
                        <p className="mock-empty">Relevance, clarity, structure, confidence, and technical depth based on the question category.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MockInterviewSession;
