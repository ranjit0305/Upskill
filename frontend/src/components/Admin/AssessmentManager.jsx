import React, { useState, useEffect } from 'react';
import { assessmentAPI } from '../../services/api';
import { Plus, List, Trash2, Calendar, AlertCircle } from 'lucide-react';
import './Admin.css';

const AssessmentManager = () => {
    const [assessments, setAssessments] = useState([]);
    const [questions, setQuestions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        type: 'aptitude',
        duration: 30,
        difficulty_level: 'medium',
        question_ids: []
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [assessRes, quesRes] = await Promise.all([
                assessmentAPI.getAssessments(),
                assessmentAPI.getQuestions()
            ]);
            setAssessments(assessRes.data);
            setQuestions(quesRes.data);
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            setLoading(false);
        }
    };

    const toggleQuestion = (id) => {
        setFormData(prev => ({
            ...prev,
            question_ids: prev.question_ids.includes(id)
                ? prev.question_ids.filter(qid => qid !== id)
                : [...prev.question_ids, id]
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (formData.question_ids.length === 0) {
            alert('Please select at least one question');
            return;
        }
        try {
            await assessmentAPI.createAssessment(formData);
            fetchData();
            setShowModal(false);
        } catch (error) {
            console.error('Error creating assessment:', error);
        }
    };

    return (
        <div className="admin-container">
            <header className="management-header">
                <div>
                    <h1>Assessment Manager</h1>
                    <p>Total Assessments: {assessments.length}</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                    <Plus size={18} /> Create New Test
                </button>
            </header>

            <div className="admin-grid">
                {assessments.map((a) => (
                    <div key={a.id} className="admin-card">
                        <span className="assessment-type">{a.type}</span>
                        <h3>{a.title}</h3>
                        <p>{a.description}</p>
                        <div className="assessment-meta" style={{ marginTop: '1rem' }}>
                            <div className="meta-item"><Calendar size={16} /> {a.duration} mins</div>
                            <div className="meta-item"><List size={16} /> {a.question_count} Questions</div>
                        </div>
                        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.5rem' }}>
                            <button className="btn btn-outline btn-full">Edit</button>
                            <button className="btn btn-icon text-danger"><Trash2 size={18} /></button>
                        </div>
                    </div>
                ))}
            </div>

            {showModal && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ maxWidth: '800px' }}>
                        <h2>Create New Assessment</h2>
                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label>Title</label>
                                <input
                                    type="text"
                                    className="input"
                                    value={formData.title}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label>Description</label>
                                <textarea
                                    className="input"
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                />
                            </div>

                            <div className="form-group grid-2">
                                <div>
                                    <label>Type</label>
                                    <select
                                        className="input"
                                        value={formData.type}
                                        onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                                    >
                                        <option value="aptitude">Aptitude</option>
                                        <option value="technical">Technical</option>
                                        <option value="coding">Coding</option>
                                    </select>
                                </div>
                                <div>
                                    <label>Duration (minutes)</label>
                                    <input
                                        type="number"
                                        className="input"
                                        value={formData.duration}
                                        onChange={(e) => setFormData({ ...formData, duration: parseInt(e.target.value) })}
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Select Questions ({formData.question_ids.length} selected)</label>
                                <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem' }}>
                                    {questions
                                        .filter(q => q.type === formData.type)
                                        .map(q => (
                                            <div
                                                key={q.id}
                                                className={`option-item ${formData.question_ids.includes(q.id) ? 'selected' : ''}`}
                                                style={{ marginBottom: '0.5rem', padding: '0.5rem 1rem' }}
                                                onClick={() => toggleQuestion(q.id)}
                                            >
                                                <span>{q.question.substring(0, 100)}...</span>
                                            </div>
                                        ))
                                    }
                                </div>
                            </div>

                            <div className="modal-footer" style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                                <button type="submit" className="btn btn-primary btn-full">Create Assessment</button>
                                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AssessmentManager;
