import React, { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Styles
import './index.css';

// Config
import { queryClient } from './config/queryClient';

// Auth Context
import { AuthProvider } from './context/AuthContext';

// Layout Components
import MainLayout from './components/layout/MainLayout';
import ErrorBoundary from './components/common/ErrorBoundary';
import { Toast } from './components/common/Toast';
import LoadingSpinner from './components/common/LoadingSpinner';

// Auth Components
import ProtectedRoute from './components/auth/ProtectedRoute';
import SessionTimeoutWarning from './components/auth/SessionTimeoutWarning';

// Lazy load pages for code splitting
const LoginPage = lazy(() => import('./pages/LoginPage'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const ClientsPage = lazy(() => import('./pages/ClientsPage'));
const ClientDetailPage = lazy(() => import('./pages/ClientDetailPage'));

// Placeholder pages
const HistoryPage: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">History</h1>
      <p className="text-gray-600">Report history page coming soon...</p>
    </div>
  );
};

const AnalyticsPage: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Analytics</h1>
      <p className="text-gray-600">Analytics dashboard coming soon...</p>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Router>
            <Toast />
            <SessionTimeoutWarning warningTime={5} sessionDuration={60} />
            <Suspense fallback={<LoadingSpinner fullScreen text="Loading page..." />}>
              <Routes>
                {/* Public routes */}
                <Route path="/login" element={<LoginPage />} />

                {/* Protected routes with layout */}
                <Route
                  path="/*"
                  element={
                    <ProtectedRoute>
                      <MainLayout>
                        <Suspense fallback={<LoadingSpinner text="Loading content..." />}>
                          <Routes>
                            <Route path="/" element={<Navigate to="/dashboard" replace />} />
                            <Route path="/dashboard" element={<Dashboard />} />
                            <Route path="/clients" element={<ClientsPage />} />
                            <Route path="/clients/:id" element={<ClientDetailPage />} />
                            <Route path="/reports" element={<ReportsPage />} />
                            <Route path="/history" element={<HistoryPage />} />
                            <Route path="/analytics" element={<AnalyticsPage />} />
                            <Route path="/settings" element={<SettingsPage />} />
                          </Routes>
                        </Suspense>
                      </MainLayout>
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </Suspense>
          </Router>
          {process.env.NODE_ENV === 'development' &&
            process.env.REACT_APP_ENABLE_REACT_QUERY_DEVTOOLS === 'true' && (
              <ReactQueryDevtools initialIsOpen={false} />
            )}
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
