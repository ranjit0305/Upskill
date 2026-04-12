import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { assessmentAPI } from '../../services/api';
import { Clock, ChevronLeft, ChevronRight, Send, AlertTriangle, ShieldCheck, Camera, Sparkles, Layout } from 'lucide-react';
import './Assessment.css';

const AssessmentView = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [assessment, setAssessment] = useState(null);
    const [questions, setQuestions] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [userAnswers, setUserAnswers] = useState({});
    const [timeLeft, setTimeLeft] = useState(0);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [result, setResult] = useState(null);
    const [showExplanations, setShowExplanations] = useState({});

    const extractCompanyId = (description) => {
        if (!description) return null;
        const match = String(description).match(/\bfor\s+([a-f0-9]{24})\b/i);
        return match ? match[1] : null;
    };

    const fetchAssessmentData = useCallback(async () => {
        try {
            setLoading(true);
            const response = await assessmentAPI.getAssessment(id);
            setAssessment(response.data);
            setTimeLeft(response.data.duration * 60);

            const questionsRes = await assessmentAPI.getAssessmentQuestions(id);
            setQuestions(questionsRes.data);
        } catch (err) {
            console.error('Error fetching assessment detail:', err);
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        fetchAssessmentData();
    }, [fetchAssessmentData]);

    useEffect(() => {
        if (!loading && !result && timeLeft > 0) {
            const timer = setInterval(() => {
                setTimeLeft(prev => {
                    if (prev <= 1) {
                        clearInterval(timer);
                        handleSubmit();
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
            return () => clearInterval(timer);
        }
    }, [loading, result, timeLeft]);

    const handleOptionSelect = (questionId, option) => {
        setUserAnswers(prev => ({
            ...prev,
            [questionId]: option
        }));
    };

    const handleSubmit = async () => {
        if (submitting) return;

        try {
            setSubmitting(true);
            const formattedAnswers = Object.entries(userAnswers).map(([qId, ans]) => ({
                question_id: qId,
                answer: ans,
                time_taken: 0
            }));

            const submissionData = {
                assessment_id: id,
                answers: formattedAnswers,
                time_taken: (assessment.duration * 60) - timeLeft
            };

            const response = await assessmentAPI.submitAssessment(submissionData);
            setResult(response.data);
        } catch (err) {
            console.error('Error submitting assessment:', err);
        } finally {
            setSubmitting(false);
        }
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const companyId = extractCompanyId(assessment?.description);
    const returnTarget = companyId ? `/company/${companyId}` : '/dashboard';

    if (loading) return <div className="loading">Initializing secure assessment environment...</div>;

    if (result) {
        return (
            <div className="results-container premium-bg">
                <main className="result-card-inner glass-card animate-fade-in">
                    <div style={{ background: 'rgba(16, 185, 129, 0.1)', width: '80px', height: '80px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem' }}>
                        <ShieldCheck size={40} color="#10b981" />
                    </div>
                    <h2 style={{ fontSize: '2rem', fontWeight: 900, marginBottom: '0.5rem' }}>Submission Successful</h2>
                    <p style={{ color: 'var(--slate)', fontWeight: 600 }}>Your performance telemetry has been analyzed.</p>
                    
                    <div className="results-score">{Math.round(result.score)}%</div>
                    
                    <div className="stats-grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2.5rem' }}>
                        <div className="glass-card" style={{ padding: '1.5rem' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: 900 }}>{Math.round(result.accuracy)}%</div>
                            <div className="stat-label">Precision</div>
                        </div>
                        <div className="glass-card" style={{ padding: '1.5rem' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: 900 }}>{formatTime(result.time_taken)}</div>
                            <div className="stat-label">Efficiency</div>
                        </div>
                    </div>

                    <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => navigate(returnTarget)}>
                        Return to Command Center <ChevronRight size={18} />
                    </button>
                </main>
            </div>
        );
    }

    const currentQuestion = questions[currentIndex];

    return (
        <div className="test-interface premium-bg">
            <header className="test-header">
                <div>
                    <h2 style={{ margin: 0, fontWeight: 900 }}>{assessment?.title}</h2>
                    <span className="question-number" style={{ margin: 0 }}>Progress Optic: {currentIndex + 1} / {questions.length}</span>
                </div>
                
                <div className="nav-right">
                    <div className="test-timer">
                        <Clock size={20} />
                        {formatTime(timeLeft)}
                    </div>
                    <button className="btn-back glass" style={{ marginBottom: 0, color: '#ef4444' }} onClick={() => {
                        if (window.confirm('Abandon assessment? Results will not be cataloged.')) {
                            navigate(companyId ? `/company/${companyId}` : '/assessments');
                        }
                    }}>
                        Terminate
                    </button>
                </div>
            </header>

            <div className="proctor-module">
                <div className="proctor-camera">
                    <div className="proctor-scan-line"></div>
                </div>
                <div className="proctor-status">
                    <div className="status-indicator">
                        <Camera size={14} className="pulse" />
                        AI Proctor Active
                    </div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--slate)', marginTop: '0.5rem', fontWeight: 600 }}>
                        Monitoring face orientation & environment stability.
                    </div>
                </div>
            </div>

            <main className="test-content animate-fade-in">
                <div className="glass-card question-card">
                    {currentQuestion ? (
                        <>
                            <span className="question-number">Problem Parameter {currentIndex + 1}</span>
                            <div className="question-text">
                                {currentQuestion.question}
                            </div>
                            
                            {(!currentQuestion.options || currentQuestion.options.length === 0) ? (
                                <div className="subjective-component">
                                    <div className="glass-card" style={{ padding: '2rem', background: 'rgba(255,255,255,0.4)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--slate)', marginBottom: '1rem', fontWeight: 700 }}>
                                            <Sparkles size={18} color="var(--primary)" />
                                            <span>BEHAVIORAL DIMENSION INTERROGATION</span>
                                        </div>
                                        <p style={{ lineHeight: 1.6, marginBottom: '1.5rem' }}>
                                            Formulate a high-impact response based on your professional trajectory.
                                        </p>
                                        <button 
                                            className="btn-back glass"
                                            style={{ marginBottom: 0 }}
                                            onClick={() => setShowExplanations(prev => ({ ...prev, [currentQuestion.id]: !prev[currentQuestion.id] }))}
                                        >
                                            {showExplanations[currentQuestion.id] ? "Hide Stratagem" : "Reveal Evaluation Stratagem"}
                                        </button>
                                        
                                        {showExplanations[currentQuestion.id] && (
                                            <div className="explanation-box animate-fade-in" style={{ background: 'white', borderRadius: '12px', marginTop: '1.5rem' }}>
                                                <strong style={{ textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Optimized Response Architecture:</strong>
                                                <p>{currentQuestion.explanation || "Detailed stratagem pending."}</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <div className="options-list">
                                    {currentQuestion.options?.map((option, idx) => {
                                        const letter = String.fromCharCode(65 + idx);
                                        const isSelected = userAnswers[currentQuestion.id] === option;
                                        return (
                                            <div
                                                key={idx}
                                                className={`option-item ${isSelected ? 'selected' : ''}`}
                                                onClick={() => handleOptionSelect(currentQuestion.id, option)}
                                            >
                                                <div className="option-letter">{letter}</div>
                                                <div className="option-text" style={{ fontWeight: 600 }}>{option}</div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="error-message">
                            <AlertTriangle color="var(--danger)" />
                            <p>Telemetry sync failure: Question pool unreachable.</p>
                        </div>
                    )}

                    <footer className="test-footer">
                        <button
                            className="btn-back glass"
                            style={{ marginBottom: 0 }}
                            disabled={currentIndex === 0}
                            onClick={() => setCurrentIndex(prev => prev - 1)}
                        >
                            <ChevronLeft /> Previous
                        </button>

                        <div style={{ display: 'flex', gap: '1rem' }}>
                            {currentIndex === questions.length - 1 ? (
                                <button
                                    className="btn btn-primary"
                                    onClick={handleSubmit}
                                    disabled={submitting}
                                >
                                    {submitting ? 'Processing...' : 'Finalize & Submit'}
                                </button>
                            ) : (
                                <button
                                    className="btn btn-primary"
                                    onClick={() => setCurrentIndex(prev => prev + 1)}
                                >
                                    Proceed <ChevronRight />
                                </button>
                            )}
                        </div>
                    </footer>
                </div>
            </main>
        </div>
    );
};

export default AssessmentView;
