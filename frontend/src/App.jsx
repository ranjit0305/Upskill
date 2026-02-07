import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import StudentDashboard from './components/Dashboard/StudentDashboard';
import AssessmentList from './components/Assessment/AssessmentList';
import AssessmentView from './components/Assessment/AssessmentView';
import AdminDashboard from './components/Dashboard/AdminDashboard';
import QuestionManager from './components/Admin/QuestionManager';
import AssessmentManager from './components/Admin/AssessmentManager';
import CompanySelection from './components/CompanyPrep/CompanySelection';
import CompanyDashboard from './components/CompanyPrep/CompanyDashboard';
import FeedbackUpload from './components/CompanyPrep/FeedbackUpload';
import './index.css';

// Protected Route Component
const ProtectedRoute = ({ children, roles = [] }) => {
    const { user, loading } = useAuth();

    if (loading) {
        return <div className="loading">Loading...</div>;
    }

    if (!user) return <Navigate to="/login" />;

    if (roles.length > 0 && !roles.includes(user.role)) {
        return <Navigate to="/dashboard" />;
    }

    return children;
};

// Public Route Component (redirect if already logged in)
const PublicRoute = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) {
        return <div className="loading">Loading...</div>;
    }

    return !user ? children : <Navigate to="/dashboard" />;
};

function AppRoutes() {
    return (
        <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route
                path="/login"
                element={
                    <PublicRoute>
                        <Login />
                    </PublicRoute>
                }
            />
            <Route
                path="/register"
                element={
                    <PublicRoute>
                        <Register />
                    </PublicRoute>
                }
            />
            <Route
                path="/dashboard"
                element={
                    <ProtectedRoute>
                        <StudentDashboard />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/assessments"
                element={
                    <ProtectedRoute>
                        <AssessmentList />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/assessments/:id"
                element={
                    <ProtectedRoute>
                        <AssessmentView />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin"
                element={
                    <ProtectedRoute roles={['admin', 'senior']}>
                        <AdminDashboard />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/questions"
                element={
                    <ProtectedRoute roles={['admin', 'senior']}>
                        <QuestionManager />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/assessments"
                element={
                    <ProtectedRoute roles={['admin', 'senior']}>
                        <AssessmentManager />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/companies"
                element={
                    <ProtectedRoute>
                        <CompanySelection />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/company/:companyId"
                element={
                    <ProtectedRoute>
                        <CompanyDashboard />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/company/:companyId/upload"
                element={
                    <ProtectedRoute roles={['admin', 'senior']}>
                        <FeedbackUpload />
                    </ProtectedRoute>
                }
            />
        </Routes>
    );
}

function App() {
    return (
        <Router>
            <AuthProvider>
                <AppRoutes />
            </AuthProvider>
        </Router>
    );
}

export default App;
