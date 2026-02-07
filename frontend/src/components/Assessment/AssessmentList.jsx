import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { assessmentAPI } from '../../services/api';
import { Clock, Book, ChevronRight, AlertCircle } from 'lucide-react';
import './Assessment.css';

const AssessmentList = () => {
    const [assessments, setAssessments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchAssessments = async () => {
            try {
                setLoading(true);
                const response = await assessmentAPI.getAssessments();
                setAssessments(response.data);
                setLoading(false);
            } catch (err) {
                console.error('Error fetching assessments:', err);
                setError('Failed to load assessments. Please try again later.');
                setLoading(false);
            }
        };

        fetchAssessments();
    }, []);

    if (loading) {
        return (
            <div className="loading-container">
                <div className="loading">Loading assessments...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="assessment-container">
                <div className="error-message">
                    <AlertCircle size={24} />
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="assessment-container">
            <div className="dashboard-header">
                <h1>Assessments</h1>
                <p>Choose an assessment to start practicing and evaluate your skills.</p>
            </div>

            {assessments.length === 0 ? (
                <div className="empty-state">
                    <Book size={48} color="#cbd5e1" />
                    <h3>No assessments available</h3>
                    <p>Check back later for new tests.</p>
                </div>
            ) : (
                <div className="assessment-grid">
                    {assessments.map((assessment) => (
                        <div key={assessment.id} className="assessment-card">
                            <span className="assessment-type">{assessment.type}</span>
                            <h3>{assessment.title}</h3>
                            <p>{assessment.description}</p>

                            <div className="assessment-meta">
                                <div className="meta-item">
                                    <Clock size={16} />
                                    <span>{assessment.duration} mins</span>
                                </div>
                                <div className="meta-item">
                                    <Book size={16} />
                                    <span>{assessment.question_count} Questions</span>
                                </div>
                            </div>

                            <div className="assessment-actions">
                                <button
                                    className="btn btn-primary w-full"
                                    onClick={() => navigate(`/assessments/${assessment.id}`)}
                                >
                                    Start Test <ChevronRight size={18} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default AssessmentList;
