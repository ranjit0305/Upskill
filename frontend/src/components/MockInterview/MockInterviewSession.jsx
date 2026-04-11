import React, { useEffect, useMemo, useState, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
    ArrowLeft, 
    CheckCircle2, 
    MessageSquareText, 
    Timer, 
    Mic, 
    MicOff, 
    Volume2, 
    VolumeX,
    StopCircle,
    Play
} from 'lucide-react';
import { mockInterviewAPI } from '../../services/api';
import VideoPreview from './VideoPreview';
import './MockInterview.css';

const MockInterviewSession = () => {
    const { sessionId } = useParams();
    const navigate = useNavigate();
    const [session, setSession] = useState(null);
    const [answer, setAnswer] = useState('');
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    
    // Voice & Speech States
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const recognitionRef = useRef(null);
    const [timer, setTimer] = useState(0);
    const timerIntervalRef = useRef(null);

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
        
        // Timer
        timerIntervalRef.current = setInterval(() => {
            setTimer(prev => prev + 1);
        }, 1000);

        return () => {
            if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
            if (recognitionRef.current) recognitionRef.current.stop();
        };
    }, [navigate, sessionId]);

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Speech to Text (STT)
    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current.stop();
            setIsListening(false);
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert('Speech Recognition is not supported in this browser.');
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event) => {
            let interimTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    setAnswer(prev => prev + ' ' + event.results[i][0].transcript);
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
        };

        recognition.onend = () => {
            setIsListening(false);
        };

        recognition.start();
        recognitionRef.current = recognition;
        setIsListening(true);
    };

    // Text to Speech (TTS)
    const speakQuestion = () => {
        if (!session?.current_question) return;

        if (isSpeaking) {
            window.speechSynthesis.cancel();
            setIsSpeaking(false);
            return;
        }

        const utterance = new SpeechSynthesisUtterance(session.current_question.prompt);
        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);
        
        setIsSpeaking(true);
        window.speechSynthesis.speak(utterance);
    };

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

        if (isListening) toggleListening();
        if (isSpeaking) window.speechSynthesis.cancel();

        try {
            setSubmitting(true);
            const response = await mockInterviewAPI.submitAnswer(sessionId, { answer });
            setAnswer('');
            if (response.data.completed) {
                navigate(`/mock-interview/session/${sessionId}/report`);
                return;
            }
            setSession(response.data.session);
            // Auto-speak next question
            // speakQuestion(); // Optional: user might find it better to click
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
                    <ArrowLeft size={18} /> Back
                </button>

                <div className="mock-session-layout">
                    <div className="mock-session-main">
                        <div className="mock-card">
                            <div className="mock-session-header">
                                <div>
                                    <div className="mock-pill active"><MessageSquareText size={14} /> {session.company_name || 'General'} Mock Interview</div>
                                    <h1 style={{ marginTop: '1rem' }}>Question {question.index + 1} of {session.total_questions}</h1>
                                </div>
                                <div className={`mock-timer ${timer > 180 ? 'warning' : ''}`}>
                                    <Timer size={16} /> {formatTime(timer)}
                                </div>
                            </div>

                            <div className="mock-progress-bar">
                                <div className="mock-progress-fill" style={{ width: `${progressPercent}%` }} />
                            </div>

                            <div className="mock-question-area">
                                <div className="mock-question-meta">
                                    <span className="category">{question.category.toUpperCase()}</span>
                                    {question.topic && <span className="topic">{question.topic}</span>}
                                    <span className="difficulty">{question.difficulty}</span>
                                </div>
                                <div className="mock-question-display">
                                    <h2>{question.prompt}</h2>
                                    <button 
                                        className={`mock-audio-btn ${isSpeaking ? 'active' : ''}`}
                                        onClick={speakQuestion}
                                        title={isSpeaking ? 'Stop speaking' : 'Listen to question'}
                                    >
                                        {isSpeaking ? <VolumeX size={18} /> : <Volume2 size={18} />}
                                    </button>
                                </div>

                                <div className="mock-answer-wrapper">
                                    <textarea
                                        className="mock-answer-box"
                                        placeholder="Type or speak your answer here. Be structured and detailed..."
                                        value={answer}
                                        onChange={(e) => setAnswer(e.target.value)}
                                    />
                                    <div className="mock-voice-controls">
                                        <button 
                                            className={`mock-mic-btn ${isListening ? 'listening' : ''}`}
                                            onClick={toggleListening}
                                            title={isListening ? 'Stop recording' : 'Start speaking'}
                                        >
                                            {isListening ? <StopCircle size={22} color="#fff" /> : <Mic size={22} />}
                                            {isListening ? 'Stop' : 'Speak Your Answer'}
                                        </button>
                                        {isListening && <div className="mock-mic-wave"><span></span><span></span><span></span></div>}
                                    </div>
                                </div>

                                <div className="mock-actions">
                                    <button className="btn btn-glass" onClick={handleFinish} disabled={submitting}>
                                        End Session
                                    </button>
                                    <button className="btn btn-primary btn-lg" onClick={handleSubmit} disabled={submitting}>
                                        {submitting ? 'Evaluating...' : 'Submit & Next Question'}
                                        <CheckCircle2 size={18} />
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div className="mock-tips-row">
                            <div className="mock-tip-card glass">
                                <h4>Pro Tip</h4>
                                <p>Try the STAR method: Situation, Task, Action, and Result. It helps in structuring behavioral answers perfectly.</p>
                            </div>
                            <div className="mock-tip-card glass">
                                <h4>Interviewer Expectation</h4>
                                <p>The evaluator looks for technical depth, clear communication, and how you handle pressure.</p>
                            </div>
                        </div>
                    </div>

                    <aside className="mock-session-side">
                        <VideoPreview />
                        <div className="mock-session-info glass">
                            <h4>Session Context</h4>
                            <div className="mock-info-list">
                                <div className="mock-info-item">
                                    <label>Mode</label>
                                    <span>{session.mode}</span>
                                </div>
                                <div className="mock-info-item">
                                    <label>Company</label>
                                    <span>{session.company_name || 'Generic'}</span>
                                </div>
                                <div className="mock-info-item">
                                    <label>Remaining</label>
                                    <span>{session.total_questions - session.current_question_index} questions left</span>
                                </div>
                            </div>
                        </div>
                    </aside>
                </div>
            </div>
        </div>
    );
};

export default MockInterviewSession;

