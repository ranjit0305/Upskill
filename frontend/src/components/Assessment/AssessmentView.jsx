import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { assessmentAPI } from '../../services/api';
import { Clock, ChevronLeft, ChevronRight, Send, AlertTriangle } from 'lucide-react';
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

            // Fetch questions specifically for this assessment
            const questionsRes = await assessmentAPI.getAssessmentQuestions(id);
            setQuestions(questionsRes.data);
            setLoading(false);
        } catch (err) {
            console.error('Error fetching assessment detail:', err);
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
                time_taken: 0 // Could track per-question time in future
            }));

            const submissionData = {
                assessment_id: id,
                answers: formattedAnswers,
                time_taken: (assessment.duration * 60) - timeLeft
            };

            const response = await assessmentAPI.submitAssessment(submissionData);
            setResult(response.data);
            setSubmitting(false);
        } catch (err) {
            console.error('Error submitting assessment:', err);
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
    const returnLabel = companyId ? 'Back to Company Dashboard' : 'Back to Dashboard';

    if (loading) return <div className="loading-container"><div className="loading">Preparing your test...</div></div>;

    if (result) {
        return (
            <div className="results-container">
                <div className="card" style={{ maxWidth: '600px', margin: '0 auto', padding: '3rem' }}>
                    <h2 style={{ color: 'var(--success)' }}>Assessment Completed!</h2>
                    <p>Your performance has been evaluated.</p>
                    <div className="results-score">{Math.round(result.score)}%</div>
                    <div className="stats-grid" style={{ marginTop: '2rem' }}>
                        <div className="stat-card">
                            <div className="stat-value">{Math.round(result.accuracy)}%</div>
                            <div className="stat-label">Accuracy</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">{formatTime(result.time_taken)}</div>
                            <div className="stat-label">Time Taken</div>
                        </div>
                    </div>
                    <button
                        className="btn btn-primary"
                        style={{ marginTop: '2rem' }}
                        onClick={() => navigate(returnTarget)}
                    >
                        {returnLabel}
                    </button>
                </div>
            </div>
        );
    }

    const currentQuestion = questions[currentIndex];

    return (
        <div className="test-interface">
            <header className="test-header">
                <div>
                    <h2 style={{ margin: 0 }}>{assessment?.title}</h2>
                    <span className="question-number">Question {currentIndex + 1} of {questions.length}</span>
                </div>
                <div className="test-timer">
                    <Clock size={24} style={{ marginRight: '0.5rem' }} />
                    {formatTime(timeLeft)}
                </div>
                <button className="btn btn-danger" onClick={() => {
                    if (window.confirm('Are you sure you want to end the test? Progress will not be saved if you leave.')) {
                        navigate(companyId ? `/company/${companyId}` : '/assessments');
                    }
                }}>
                    Quit Test
                </button>
            </header>

            <main className="test-content">
                {currentQuestion ? (
                    <>
                        <div className="question-text">
                            {currentQuestion.question}
                        </div>
                        {(!currentQuestion.options || currentQuestion.options.length === 0) ? (
                            <div className="subjective-component">
                                <div className="card subjective-card">
                                    <div className="subjective-header">
                                        <AlertTriangle size={18} />
                                        <span>This is an open-ended/behavioral question.</span>
                                    </div>
                                    <p className="subjective-prompt">
                                        Prepare your response mentally or write it down. Focus on your specific experiences and results.
                                    </p>
                                    <button 
                                        className="btn btn-outline btn-sm"
                                        onClick={() => setShowExplanations(prev => ({
                                            ...prev,
                                            [currentQuestion.id]: !prev[currentQuestion.id]
                                        }))}
                                    >
                                        {showExplanations[currentQuestion.id] ? "Hide Guide" : "Show Model Answer / Guide"}
                                    </button>
                                    
                                    {showExplanations[currentQuestion.id] && (
                                        <div className="explanation-box animate-fade-in">
                                            <strong>Model Answer / Approach:</strong>
                                            <p>{currentQuestion.explanation || "No specific guide provided for this question."}</p>
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
                                            <div className="option-text">{option}</div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </>
                ) : (
                    <div className="error-message">
                        <AlertTriangle />
                        <p>Questions not found for this assessment.</p>
                    </div>
                )}

                <div className="test-footer">
                    <button
                        className="btn btn-outline"
                        disabled={currentIndex === 0}
                        onClick={() => setCurrentIndex(prev => prev - 1)}
                    >
                        <ChevronLeft /> Previous
                    </button>

                    {currentIndex === questions.length - 1 ? (
                        <button
                            className="btn btn-primary"
                            onClick={handleSubmit}
                            disabled={submitting}
                        >
                            {submitting ? 'Submitting...' : 'Finish & Submit'} <Send size={18} />
                        </button>
                    ) : (
                        <button
                            className="btn btn-primary"
                            onClick={() => setCurrentIndex(prev => prev + 1)}
                        >
                            Next <ChevronRight />
                        </button>
                    )}
                </div>
            </main>
        </div>
    );
};

export default AssessmentView;
