import React, { useState, useEffect } from 'react';
import { assessmentAPI } from '../../services/api';
import { Plus, Search, Filter, Edit2, Trash2, X, Check } from 'lucide-react';
import './Admin.css';

const QuestionManager = () => {
    const [questions, setQuestions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [currentQuestion, setCurrentQuestion] = useState(null);
    const [formData, setFormData] = useState({
        type: 'aptitude',
        category: '',
        difficulty: 'easy',
        question: '',
        options: ['', '', '', ''],
        correct_answer: '',
        explanation: '',
        tags: '',
        companies: ''
    });

    useEffect(() => {
        fetchQuestions();
    }, []);

    const fetchQuestions = async () => {
        try {
            const response = await assessmentAPI.getQuestions();
            setQuestions(response.data);
        } catch (error) {
            console.error('Error fetching questions:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = (q) => {
        setCurrentQuestion(q);
        setFormData({
            ...q,
            tags: q.tags.join(', '),
            companies: q.companies.join(', ')
        });
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...formData,
                tags: formData.tags.split(',').map(s => s.trim()),
                companies: formData.companies.split(',').map(s => s.trim())
            };

            if (currentQuestion) {
                // Update logic (to be implemented in backend if missing)
                console.log('Update Question:', payload);
            } else {
                await assessmentAPI.createQuestion(payload);
            }
            fetchQuestions();
            setShowModal(false);
        } catch (error) {
            console.error('Error saving question:', error);
        }
    };

    return (
        <div className="admin-container">
            <header className="management-header">
                <div>
                    <h1>Question Manager</h1>
                    <p>Total Questions: {questions.length}</p>
                </div>
                <button className="btn btn-primary" onClick={() => {
                    setCurrentQuestion(null);
                    setFormData({
                        type: 'aptitude',
                        category: '',
                        difficulty: 'easy',
                        question: '',
                        options: ['', '', '', ''],
                        correct_answer: '',
                        explanation: '',
                        tags: '',
                        companies: ''
                    });
                    setShowModal(true);
                }}>
                    <Plus size={18} /> Add New Question
                </button>
            </header>

            <table className="data-table">
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Question</th>
                        <th>Category</th>
                        <th>Difficulty</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {questions.map((q) => (
                        <tr key={q.id}>
                            <td><span className="assessment-type">{q.type}</span></td>
                            <td>{q.question.substring(0, 60)}...</td>
                            <td>{q.category}</td>
                            <td>{q.difficulty}</td>
                            <td>
                                <button className="btn btn-icon" onClick={() => handleEdit(q)}><Edit2 size={16} /></button>
                                <button className="btn btn-icon text-danger"><Trash2 size={16} /></button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {showModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h2>{currentQuestion ? 'Edit Question' : 'Add New Question'}</h2>
                        <form onSubmit={handleSubmit}>
                            <div className="form-group grid-2">
                                <div>
                                    <label>Type</label>
                                    <select
                                        value={formData.type}
                                        onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                                        className="input"
                                    >
                                        <option value="aptitude">Aptitude</option>
                                        <option value="technical">Technical</option>
                                        <option value="coding">Coding</option>
                                    </select>
                                </div>
                                <div>
                                    <label>Difficulty</label>
                                    <select
                                        value={formData.difficulty}
                                        onChange={(e) => setFormData({ ...formData, difficulty: e.target.value })}
                                        className="input"
                                    >
                                        <option value="easy">Easy</option>
                                        <option value="medium">Medium</option>
                                        <option value="hard">Hard</option>
                                    </select>
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Category (e.g., quant, logical, os)</label>
                                <input
                                    type="text"
                                    className="input"
                                    value={formData.category}
                                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                                />
                            </div>

                            <div className="form-group">
                                <label>Question Text</label>
                                <textarea
                                    className="input"
                                    rows="3"
                                    value={formData.question}
                                    onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                                />
                            </div>

                            <div className="form-group">
                                <label>Options</label>
                                {formData.options.map((opt, i) => (
                                    <input
                                        key={i}
                                        type="text"
                                        className="input"
                                        style={{ marginBottom: '0.5rem' }}
                                        value={opt}
                                        placeholder={`Option ${String.fromCharCode(65 + i)}`}
                                        onChange={(e) => {
                                            const newOpts = [...formData.options];
                                            newOpts[i] = e.target.value;
                                            setFormData({ ...formData, options: newOpts });
                                        }}
                                    />
                                ))}
                            </div>

                            <div className="form-group">
                                <label>Correct Answer (Exact text of the option)</label>
                                <input
                                    type="text"
                                    className="input"
                                    value={formData.correct_answer}
                                    onChange={(e) => setFormData({ ...formData, correct_answer: e.target.value })}
                                />
                            </div>

                            <div className="modal-footer" style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                                <button type="submit" className="btn btn-primary btn-full">Save Question</button>
                                <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default QuestionManager;
