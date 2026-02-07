import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { companyAPI } from '../../services/api';
import { Upload, FileText, CheckCircle, XCircle, Loader } from 'lucide-react';
import './CompanyPrep.css';

const FeedbackUpload = () => {
    const { companyId } = useParams();
    const { user } = useAuth();
    const navigate = useNavigate();
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    const handleFileChange = (e) => {
        const selectedFiles = Array.from(e.target.files);
        const validFiles = selectedFiles.filter(file => {
            const ext = file.name.split('.').pop().toLowerCase();
            return ['pdf', 'docx', 'doc'].includes(ext);
        });

        if (validFiles.length > 0) {
            setFiles(validFiles);
            setMessage({ type: '', text: '' });
        } else if (selectedFiles.length > 0) {
            setFiles([]);
            setMessage({ type: 'error', text: 'Please select valid PDF or Word documents.' });
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (files.length === 0) return;

        setUploading(true);
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        formData.append('uploader_id', user.id);

        try {
            const response = await companyAPI.uploadFeedback(companyId, formData);
            setMessage({ type: 'success', text: `${files.length} file(s) uploaded and processed successfully!` });
            setTimeout(() => navigate(`/company/${companyId}`), 2000);
        } catch (error) {
            console.error('Upload error details:', error.response?.data);
            const errorData = error.response?.data?.detail;
            let errorMsg = 'Failed to upload feedback. ';

            if (typeof errorData === 'string') {
                errorMsg += errorData;
            } else if (Array.isArray(errorData)) {
                errorMsg += errorData.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
            } else {
                errorMsg += error.message || 'Please check file sizes or connection.';
            }

            setMessage({ type: 'error', text: errorMsg });
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="upload-container container">
            <div className="upload-card card">
                <h1>Upload Interview Feedback</h1>
                <p>Provide previous Zoho interview experiences to help students prepare better.</p>

                <form onSubmit={handleSubmit} className="upload-form">
                    <div className={`dropzone ${files.length > 0 ? 'has-file' : ''}`}>
                        <input
                            type="file"
                            id="fileInput"
                            onChange={handleFileChange}
                            disabled={uploading}
                            multiple
                        />
                        <label htmlFor="fileInput">
                            {uploading ? (
                                <Loader className="spin" size={48} />
                            ) : files.length > 0 ? (
                                <CheckCircle size={48} color="var(--success)" />
                            ) : (
                                <Upload size={48} color="#64748b" />
                            )}
                            <div className="label-text">
                                {files.length > 0
                                    ? `${files.length} file(s) selected: ${files.map(f => f.name).join(', ')}`
                                    : "Click to select or drag PDF/Word files (Multiple supported)"}
                            </div>
                        </label>
                    </div>

                    {message.text && (
                        <div className={`message ${message.type}`}>
                            {message.type === 'success' ? <CheckCircle size={16} /> : <XCircle size={16} />}
                            {message.text}
                        </div>
                    )}

                    <div className="upload-actions">
                        <button
                            type="button"
                            className="btn btn-outline"
                            onClick={() => navigate(`/company/${companyId}`)}
                            disabled={uploading}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={files.length === 0 || uploading}
                        >
                            {uploading ? 'Processing...' : 'Upload & Process'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default FeedbackUpload;
