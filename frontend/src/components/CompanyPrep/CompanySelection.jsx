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

    if (loading) return <div className="loading">Loading companies...</div>;

    const isAdmin = user?.role === 'admin' || user?.role === 'senior';

    return (
        <div className="company-selection-container container">
            <header className="selection-header">
                <div className="header-content">
                    <div>
                        <button className="btn-back" onClick={() => navigate('/dashboard')}>
                            <ArrowLeft size={16} /> Back to Dashboard
                        </button>
                        <h1>Company-Wise Preparation</h1>
                        <p>Select a company to start your targeted preparation</p>
                    </div>
                    {isAdmin && (
                        <button className="btn-primary" onClick={() => setShowAddModal(true)}>
                            <Plus size={18} /> Add Company
                        </button>
                    )}
                </div>
            </header>

            <div className="search-bar">
                <Search size={20} color="#64748b" />
                <input
                    type="text"
                    placeholder="Search companies..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>

            <div className="company-grid">
                {filteredCompanies.map(company => (
                    <div
                        key={company._id}
                        className="company-card"
                        onClick={() => navigate(`/company/${company._id}`)}
                    >
                        <div className="company-logo">
                            {company.logo_url ? (
                                <img src={company.logo_url} alt={company.name} />
                            ) : (
                                <Building2 size={40} color="var(--primary)" />
                            )}
                        </div>
                        <div className="company-info">
                            <h3>{company.name}</h3>
                            <p>{company.description.substring(0, 100)}...</p>
                            <div className="company-tags">
                                {company.important_areas?.slice(0, 3).map(area => (
                                    <span key={area} className="tag">{area}</span>
                                ))}
                            </div>
                        </div>
                        <div className="card-footer">
                            <span>Start Prep</span>
                            <ChevronRight size={16} />
                        </div>
                    </div>
                ))}
            </div>

            {showAddModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <button className="modal-close" onClick={() => setShowAddModal(false)}>
                            <X size={24} />
                        </button>
                        <h2>Add New Company</h2>
                        <form onSubmit={handleCreateCompany}>
                            <div className="form-group">
                                <label>Company Name</label>
                                <input
                                    type="text"
                                    required
                                    value={newCompany.name}
                                    onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })}
                                />
                            </div>
                            <div className="form-group">
                                <label>Description</label>
                                <textarea
                                    required
                                    value={newCompany.description}
                                    onChange={(e) => setNewCompany({ ...newCompany, description: e.target.value })}
                                />
                            </div>
                            <div className="form-group">
                                <label>Logo URL (Optional)</label>
                                <input
                                    type="url"
                                    value={newCompany.logo_url}
                                    onChange={(e) => setNewCompany({ ...newCompany, logo_url: e.target.value })}
                                />
                            </div>
                            <div className="form-group">
                                <label>Website (Optional)</label>
                                <input
                                    type="url"
                                    value={newCompany.website}
                                    onChange={(e) => setNewCompany({ ...newCompany, website: e.target.value })}
                                />
                            </div>
                            <button type="submit" className="btn-primary">Create Company</button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CompanySelection;
