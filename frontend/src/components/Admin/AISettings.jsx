import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminAPI } from '../../services/api';
import { Save, ArrowLeft, Cpu, Sliders, MessageSquare, ShieldCheck, RefreshCw } from 'lucide-react';
import '../Admin/Admin.css';

const AISettings = () => {
    const [settings, setSettings] = useState({
        interview_prompt: '',
        coding_evaluation_rules: '',
        assessment_weights: { aptitude: 0.3, technical: 0.4, coding: 0.3 }
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const response = await adminAPI.getSettings('ai');
                setSettings(response.data);
            } catch (error) {
                console.error('Error fetching AI settings:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchSettings();
    }, []);

    const handleSave = async () => {
        setSaving(true);
        setMessage(null);
        try {
            await adminAPI.updateSettings('ai', settings);
            setMessage({ type: 'success', text: 'AI configurations deployed successfully.' });
        } catch (error) {
            setMessage({ type: 'error', text: 'Deployment failed. Check system logs.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 5000);
        }
    };

    if (loading) return <div className="loading">Syncing platform parameters...</div>;

    return (
        <div className="admin-container premium-bg">
            <div className="container animate-fade-in">
                <header className="management-header">
                    <div>
                        <button className="mock-back" onClick={() => navigate('/admin')}>
                            <ArrowLeft size={16} /> Backend control
                        </button>
                        <h1>AI Orchestration</h1>
                        <p style={{ color: 'var(--slate)', fontSize: '1.1rem' }}>Fine-tune LLM behavior and evaluation heuristics.</p>
                    </div>
                    <div className="header-actions">
                        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                            {saving ? <RefreshCw className="spin" size={18} /> : <Save size={18} />}
                            Deploy Changes
                        </button>
                    </div>
                </header>

                {message && (
                    <div className={`sync-banner ${message.type} glass-card`} style={{ padding: '1rem', marginBottom: '2rem', borderLeft: `4px solid var(--${message.type === 'success' ? 'success' : 'danger'})` }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            {message.type === 'success' ? <ShieldCheck size={20} color="var(--success)" /> : <Sliders size={20} color="var(--danger)" />}
                            <span style={{ fontWeight: 600 }}>{message.text}</span>
                        </div>
                    </div>
                )}

                <div className="admin-grid" style={{ gridTemplateColumns: '1fr' }}>
                    {/* Interview System Prompt */}
                    <div className="admin-card glass-card">
                        <div className="section-title" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <MessageSquare size={20} color="var(--primary)" />
                            <h3 style={{ margin: 0, fontWeight: 800 }}>Primary Interview Persona</h3>
                        </div>
                        <p style={{ color: 'var(--slate)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                            This prompt defines the personality and guidelines for the AI during the Mock Interview module.
                        </p>
                        <textarea
                            className="mock-answer-box"
                            style={{ minHeight: '150px', padding: '1.5rem', fontSize: '1rem', lineHeight: 1.6 }}
                            value={settings.interview_prompt}
                            onChange={(e) => setSettings({ ...settings, interview_prompt: e.target.value })}
                            placeholder="Define the interviewer persona here..."
                        />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
                        {/* Coding Evaluation Logic */}
                        <div className="admin-card glass-card">
                            <div className="section-title" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <Cpu size={20} color="var(--primary)" />
                                <h3 style={{ margin: 0, fontWeight: 800 }}>Code Evaluation Heuristics</h3>
                            </div>
                            <textarea
                                className="mock-answer-box"
                                style={{ minHeight: '120px', padding: '1.25rem' }}
                                value={settings.coding_evaluation_rules}
                                onChange={(e) => setSettings({ ...settings, coding_evaluation_rules: e.target.value })}
                                placeholder="Rules for AI code analysis..."
                            />
                        </div>

                        {/* Weight Distribution */}
                        <div className="admin-card glass-card">
                            <div className="section-title" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <Sliders size={20} color="var(--primary)" />
                                <h3 style={{ margin: 0, fontWeight: 800 }}>Readiness Weightages</h3>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                                {Object.entries(settings.assessment_weights || {}).map(([key, value]) => (
                                    <div key={key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <label style={{ textTransform: 'capitalize', fontWeight: 700, color: 'var(--slate)' }}>{key}</label>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', width: '60%' }}>
                                            <input
                                                type="range"
                                                min="0"
                                                max="1"
                                                step="0.1"
                                                value={value}
                                                onChange={(e) => setSettings({
                                                    ...settings,
                                                    assessment_weights: { ...settings.assessment_weights, [key]: parseFloat(e.target.value) }
                                                })}
                                                style={{ flex: 1 }}
                                            />
                                            <span style={{ fontWeight: 800, minWidth: '40px' }}>{Math.round(value * 100)}%</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <p style={{ marginTop: '1.5rem', fontSize: '0.75rem', color: 'var(--slate)', fontStyle: 'italic' }}>
                                These weights determine the final "Readiness Score" calculation for companies.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AISettings;
