import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { companyAPI } from '../../services/api';
import { Building2, ChevronRight, Search } from 'lucide-react';
import './CompanyPrep.css';

const CompanySelection = () => {
    const [companies, setCompanies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
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
        fetchCompanies();
    }, []);

    const filteredCompanies = companies.filter(company =>
        company.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) return <div className="loading">Loading companies...</div>;

    return (
        <div className="company-selection-container container">
            <header className="selection-header">
                <h1>Company-Wise Preparation</h1>
                <p>Select a company to start your targeted preparation</p>
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
        </div>
    );
};

export default CompanySelection;
