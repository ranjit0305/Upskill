import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { assessmentAPI } from '../../services/api';
import { Clock, ChevronLeft, ChevronRight, Play, Send, CheckCircle, XCircle, Loader, Code } from 'lucide-react';
import CodeEditor from './CodeEditor';
import './Assessment.css';

const CodingAssessmentView = () => {
    const { id } = useParams();
    const navigate = useNavigate();

    const [assessment, setAssessment] = useState(null);
    const [questions, setQuestions] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [codeState, setCodeState] = useState({}); // { [questionId]: { code, language } }
    const [testResults, setTestResults] = useState({}); // { [questionId]: results }
    const [timeLeft, setTimeLeft] = useState(0);
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const [submittingQuestion, setSubmittingQuestion] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [submissionResults, setSubmissionResults] = useState({}); // { [questionId]: { score, passed, passed_test_cases, total_test_cases } }
    const [result, setResult] = useState(null);

    const extractCompanyId = (description) => {
        if (!description) return null;
        const match = String(description).match(/\bfor\s+([a-f0-9]{24})\b/i);
        return match ? match[1] : null;
    };

    const languages = [
        { label: 'Python', value: 'python', default: 'import sys\n\ndef solution():\n    # Write your code here\n    # Use sys.stdin.read() or input() if needed\n    pass\n\nif __name__ == "__main__":\n    solution()' },
        { label: 'Java', value: 'java', default: 'import java.util.*;\nimport java.io.*;\n\nclass Main {\n    public static void main(String[] args) {\n        // Write your code here\n        // System.out.println("Hello");\n    }\n}' },
        { label: 'C++', value: 'cpp', default: '#include <iostream>\n#include <vector>\n#include <string>\n\nusing namespace std;\n\nint main() {\n    // Write your code here\n    return 0;\n}' },
        { label: 'JavaScript', value: 'javascript', default: 'function solution() {\n    // Write your code here\n}\n\n// To run the solution:\n// solution();' }
    ];

    const fetchAssessmentData = useCallback(async () => {
        try {
            setLoading(true);
            const response = await assessmentAPI.getAssessment(id);
            setAssessment(response.data);
            setTimeLeft(response.data.duration * 60);

            const questionsRes = await assessmentAPI.getAssessmentQuestions(id);
            setQuestions(questionsRes.data);

            // Initialize code state
            const initialCode = {};
            questionsRes.data.forEach(q => {
                initialCode[q.id] = {
                    code: languages[0].default,
                    language: 'python'
                };
            });
            setCodeState(initialCode);
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

    const handleCodeChange = (newCode) => {
        setCodeState(prev => ({
            ...prev,
            [questions[currentIndex].id]: {
                ...prev[questions[currentIndex].id],
                code: newCode
            }
        }));
    };

    const handleLanguageChange = (lang) => {
        const langObj = languages.find(l => l.value === lang);
        setCodeState(prev => ({
            ...prev,
            [questions[currentIndex].id]: {
                code: langObj.default,
                language: lang
            }
        }));
    };

    const handleRunCode = async () => {
        const currentQ = questions[currentIndex];
        const state = codeState[currentQ.id];

        try {
            setRunning(true);
            const response = await assessmentAPI.runCode({
                code: state.code,
                language: state.language,
                stdin: currentQ.sample_input || currentQ.test_cases?.[0]?.input || "",
                expected_output: currentQ.sample_output || currentQ.test_cases?.[0]?.output || ""
            });

            setTestResults(prev => ({
                ...prev,
                [currentQ.id]: response.data
            }));
            setRunning(false);
        } catch (err) {
            console.error('Run failed:', err);
            setRunning(false);
        }
    };

    const handleSubmit = async () => {
        if (submitting) return;

        try {
            setSubmitting(true);
            const formattedAnswers = Object.entries(codeState).map(([qId, state]) => ({
                question_id: qId,
                code: state.code,
                language: state.language,
                time_taken: 0
            }));

            const submissionData = {
                assessment_id: id,
                answers: formattedAnswers
            };

            const response = await assessmentAPI.submitAssessment(submissionData);
            setResult(response.data);
            setSubmitting(false);
        } catch (err) {
            console.error('Error submitting:', err);
            setSubmitting(false);
        }
    };

    const handleSubmitQuestion = async () => {
        const currentQ = questions[currentIndex];
        const state = codeState[currentQ.id];

        try {
            setSubmittingQuestion(true);
            const response = await assessmentAPI.submitQuestionAnswer(id, currentQ.id, {
                code: state.code,
                language: state.language
            });

            setSubmissionResults(prev => ({
                ...prev,
                [currentQ.id]: response.data
            }));
            setSubmittingQuestion(false);
        } catch (err) {
            console.error('Question submission failed:', err);
            setSubmittingQuestion(false);
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

    if (loading) return <div className="loading-container"><div className="loading">Preparing workspace...</div></div>;

    if (result) {
        return (
            <div className="results-container">
                <div className="card" style={{ maxWidth: '800px', margin: '0 auto', padding: '3rem' }}>
                    <h2 style={{ color: 'var(--success)', textAlign: 'center' }}>Coding Challenge Completed!</h2>
                    <div className="results-grid" style={{ marginTop: '2rem' }}>
                        <div className="stat-card">
                            <div className="stat-value">{Math.round(result.total_score)}%</div>
                            <div className="stat-label">Total Score</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">{Math.round(result.coding_score)}%</div>
                            <div className="stat-label">Coding Score</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">{formatTime(result.time_taken)}</div>
                            <div className="stat-label">Final Time</div>
                        </div>
                    </div>
                    <button
                        className="btn btn-primary"
                        style={{ marginTop: '3rem', width: '100%' }}
                        onClick={() => navigate(returnTarget)}
                    >
                        {returnLabel}
                    </button>
                </div>
            </div>
        );
    }

    const currentQuestion = questions[currentIndex];
    const currentState = codeState[currentQuestion?.id];
    const currentRunResult = testResults[currentQuestion?.id];

    return (
        <div className="coding-interface">
            <header className="test-header">
                <div className="header-left">
                    <button className="btn-icon" onClick={() => navigate(companyId ? `/company/${companyId}` : -1)}><ChevronLeft /></button>
                    <h2>{assessment?.title}</h2>
                </div>
                <div className="test-timer">
                    <Clock size={20} />
                    <span>{formatTime(timeLeft)}</span>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
                        {submitting ? <Loader className="spin" /> : <><Send size={18} /> Finish</>}
                    </button>
                </div>
            </header>

            <div className="coding-workspace">
                <div className="problem-panel">
                    <div className="panel-header">
                        <span className="badge">Q{currentIndex + 1}</span>
                        <span className={`difficulty ${currentQuestion?.difficulty}`}>{currentQuestion?.difficulty}</span>
                    </div>
                    <div className="problem-content">
                        <h3>Problem Description</h3>
                        <p>{currentQuestion?.question}</p>

                        {currentQuestion?.sample_input && (
                            <div className="example-box">
                                <div className="example-item">
                                    <strong>Sample Input:</strong>
                                    <code>{currentQuestion.sample_input}</code>
                                </div>
                                <div className="example-item">
                                    <strong>Sample Output:</strong>
                                    <code>{currentQuestion.sample_output}</code>
                                </div>
                            </div>
                        )}

                        <div className="test-case-hints">
                            <div className="tc-count">
                                <strong>Total Test Cases:</strong> {currentQuestion?.test_cases_count || 0}
                            </div>
                            {submissionResults[currentQuestion?.id] && (
                                <div className={`passed-indicator ${submissionResults[currentQuestion.id].passed ? 'all-passed' : 'partial-passed'}`}>
                                    <CheckCircle size={14} />
                                    <span>Passed {submissionResults[currentQuestion.id].passed_test_cases} / {submissionResults[currentQuestion.id].total_test_cases}</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <div className="editor-panel">
                    <div className="editor-controls">
                        <select
                            value={currentState?.language}
                            onChange={(e) => handleLanguageChange(e.target.value)}
                            className="select-lang"
                        >
                            {languages.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
                        </select>
                        <button className="btn btn-outline" onClick={handleRunCode} disabled={running}>
                            {running ? <Loader className="spin" size={16} /> : <><Play size={16} /> Run Code</>}
                        </button>
                        <button className="btn btn-primary" onClick={handleSubmitQuestion} disabled={submittingQuestion}>
                            {submittingQuestion ? <Loader className="spin" size={16} /> : <><CheckCircle size={16} title="Evaluate all test cases" /> Submit Question</>}
                        </button>
                    </div>
                    <div className="editor-wrapper">
                        <CodeEditor
                            value={currentState?.code}
                            onChange={handleCodeChange}
                            language={currentState?.language}
                        />
                    </div>
                    <div className="output-panel">
                        <div className="output-header">Console Output</div>
                        <div className="output-content">
                            {currentRunResult ? (
                                <div className={`result-box ${currentRunResult.status?.id === 3 ? 'success' : 'error'}`}>
                                    <div className="result-status">
                                        {currentRunResult.status?.id === 3 ? <CheckCircle size={16} /> : <XCircle size={16} />}
                                        {currentRunResult.status?.description}
                                    </div>
                                    {currentRunResult.stdout && <pre>Stdout: {currentRunResult.stdout}</pre>}
                                    {currentRunResult.stderr && <pre className="error">Stderr: {currentRunResult.stderr}</pre>}
                                    {currentRunResult.compile_output && <pre className="error">Compile Error: {currentRunResult.compile_output}</pre>}
                                </div>
                            ) : currentState && submissionResults[questions[currentIndex]?.id] ? (
                                <div className={`result-box submission-result ${submissionResults[questions[currentIndex]?.id].passed ? 'success' : 'warning'}`}>
                                    <div className="result-status">
                                        {submissionResults[questions[currentIndex]?.id].passed ? <CheckCircle size={18} /> : <XCircle size={18} />}
                                        <strong>Submission Result: {submissionResults[questions[currentIndex]?.id].score}% Score</strong>
                                    </div>
                                    <div className="test-case-summary">
                                        Passed {submissionResults[questions[currentIndex]?.id].passed_test_cases} / {submissionResults[questions[currentIndex]?.id].total_test_cases} Hidden Test Cases
                                    </div>
                                    {submissionResults[questions[currentIndex]?.id].passed ?
                                        <p className="success-msg">Great! You've successfully passed all test cases for this question.</p> :
                                        <p className="hint-msg">Some hidden test cases failed. Try checking for edge cases or optimizing your code.</p>
                                    }
                                </div>
                            ) : (
                                <div className="empty-placeholder">Run code for sample testing or Submit to evaluate all hidden cases.</div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            <footer className="workspace-footer">
                <button
                    className="btn btn-outline"
                    disabled={currentIndex === 0}
                    onClick={() => setCurrentIndex(prev => prev - 1)}
                >
                    <ChevronLeft /> Previous
                </button>
                <div className="progress-dots">
                    {questions.map((_, idx) => (
                        <div key={idx} className={`dot ${idx === currentIndex ? 'active' : ''}`} />
                    ))}
                </div>
                <button
                    className="btn btn-outline"
                    disabled={currentIndex === questions.length - 1}
                    onClick={() => setCurrentIndex(prev => prev + 1)}
                >
                    Next <ChevronRight />
                </button>
            </footer>
        </div>
    );
};

export default CodingAssessmentView;
