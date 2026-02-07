import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Remove Content-Type for FormData to let browser set it with boundary
        if (config.data instanceof FormData) {
            delete config.headers['Content-Type'];
        }

        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor to handle errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Auth API
export const authAPI = {
    register: (data) => api.post('/auth/register', data),
    login: (data) => api.post('/auth/login', data),
    getCurrentUser: () => api.get('/auth/me'),
    refreshToken: (token) => api.post('/auth/refresh', {}, {
        headers: { Authorization: `Bearer ${token}` }
    }),
};

// Assessment API
export const assessmentAPI = {
    getQuestions: (params) => api.get('/assessment/questions', { params }),
    createQuestion: (data) => api.post('/assessment/questions', data),
    getAssessments: () => api.get('/assessment/assessments'),
    getAssessment: (id) => api.get(`/assessment/assessments/${id}`),
    createAssessment: (data) => api.post('/assessment/assessments', data),
    submitAssessment: (data) => api.post('/assessment/submissions', data),
    getSubmissions: () => api.get('/assessment/submissions'),
    deleteQuestion: (id) => api.delete(`/assessment/questions/${id}`),
    deleteAssessment: (id) => api.delete(`/assessment/assessments/${id}`),
};

// Performance API
export const performanceAPI = {
    getPerformance: () => api.get('/performance/me'),
    getReadinessScore: () => api.get('/performance/readiness'),
};

// Admin API
export const adminAPI = {
    getStats: () => api.get('/admin/stats'),
    getDistribution: () => api.get('/admin/distribution'),
};

// Company Preparation API
export const companyAPI = {
    getCompanies: () => api.get('/companies'),
    getDashboard: (companyId, userId) => api.get(`/companies/${companyId}/dashboard`, { params: { user_id: userId } }),
    uploadFeedback: (companyId, formData) => api.post(`/companies/${companyId}/feedback`, formData),
};

export default api;
