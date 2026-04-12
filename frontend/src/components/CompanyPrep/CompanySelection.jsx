import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { companyAPI } from '../../services/api';
import { ArrowLeft, Building2, ChevronRight, Search, Plus, X } from 'lucide-react';
import './CompanyPrep.css';

const CompanySelection = () => {
    const [companies, setCompanies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [showAddModal, setShowAddModal] = useState(false);
    const [newCompany, setNewCompany] = useState({ name: '', description: '', logo_url: '', website: '' });
    const { user } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        fetchCompanies();
    }, []);

    const fetchCompanies = async () => {
        try {
            const response = await companyAPI.getCompanies();
            setCompanies(response.data);
        } catch (error) {
            console.error('Error fetching companies:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateCompany = async (e) => {
        e.preventDefault();
        try {
            await companyAPI.createCompany(newCompany);
            setShowAddModal(false);
            setNewCompany({ name: '', description: '', logo_url: '', website: '' });
            fetchCompanies(); // Refresh list
        } catch (error) {
            alert(error.response?.data?.detail || 'Failed to create company');
        }
    };

    const filteredCompanies = companies.filter(company =>
        company.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) return <div className="loading">Mapping company landscapes...</div>;

    const isAdmin = user?.role === 'admin' || user?.role === 'senior';

    return (
        <div className="company-selection-container premium-bg">
            <div className="container animate-fade-in">
                <header className="selection-header">
                    <button className="mock-back" onClick={() => navigate('/dashboard')}>
                        <ArrowLeft size={16} /> Dashboard
                    </button>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                        <h1>Targeted Preparation</h1>
                        {isAdmin && (
                            <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
                                <Plus size={18} /> Add Target Company
                            </button>
                        )}
                    </div>
                </header>

                <div className="search-bar">
                    <Search size={20} color="var(--primary)" />
                    <input
                        type="text"
                        placeholder="Search for a company (e.g. Google, Amazon, Microsoft)..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        style={{ background: 'transparent', outline: 'none', border: 'none', width: '100%', marginLeft: '1rem', fontSize: '1.1rem' }}
                    />
                </div>

                <div className="company-grid">
                    {filteredCompanies.map(company => (
                        <div
                            key={company._id}
                            className="company-card"
                            onClick={() => navigate(`/company/${company._id}`)}
                        >
                            <div className="company-logo" style={{ marginBottom: '1.5rem', background: 'white', padding: '0.75rem', borderRadius: '16px', display: 'inline-flex', boxShadow: '0 4px 12px rgba(0,0,0,0.03)' }}>
                                {company.logo_url ? (
                                    <img src={company.logo_url} alt={company.name} style={{ height: '40px', objectFit: 'contain' }} />
                                ) : (
                                    <Building2 size={32} color="var(--primary)" />
                                )}
                            </div>
                            <div className="company-info">
                                <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--dark)' }}>{company.name}</h3>
                                <p style={{ color: 'var(--slate)', fontSize: '0.95rem', lineHeight: 1.6, margin: '0.5rem 0 1.25rem' }}>
                                    {company.description.substring(0, 100)}...
                                </p>
                                <div className="company-tags">
                                    {company.important_areas?.slice(0, 3).map(area => (
                                        <span key={area} className="mock-mode-badge" style={{ margin: 0 }}>{area}</span>
                                    ))}
                                </div>
                            </div>
                            <div className="card-footer" style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid rgba(0,0,0,0.05)', display: 'flex', justifyContent: 'space-between', color: 'var(--primary)', fontWeight: 800 }}>
                                <span>Configure Prep</span>
                                <ChevronRight size={18} />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {showAddModal && (
                <div className="modal-overlay glass" style={{ position: 'fixed', inset: 0, zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div className="glass-card" style={{ maxWidth: '500px', width: '90%', animation: 'fadeSlideIn 0.3s' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                            <h2 style={{ margin: 0, fontWeight: 900 }}>New Target</h2>
                            <button className="btn-back" style={{ marginBottom: 0 }} onClick={() => setShowAddModal(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleCreateCompany} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                            <div className="form-group">
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 700, fontSize: '0.85rem', color: 'var(--slate)' }}>COMPANY NAME</label>
                                <input
                                    className="mock-answer-box"
                                    style={{ minHeight: 'auto', padding: '0.75rem 1rem' }}
                                    type="text"
                                    required
                                    value={newCompany.name}
                                    onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })}
                                />
                            </div>
                            <div className="form-group">
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 700, fontSize: '0.85rem', color: 'var(--slate)' }}>DESCRIPTION</label>
                                <textarea
                                    className="mock-answer-box"
                                    style={{ minHeight: '100px', padding: '0.75rem 1rem' }}
                                    required
                                    value={newCompany.description}
                                    onChange={(e) => setNewCompany({ ...newCompany, description: e.target.value })}
                                />
                            </div>
                            <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>Create Landscape</button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};


export default CompanySelection;
