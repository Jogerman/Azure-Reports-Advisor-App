import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Styles
import './index.css';

// Auth Context
import { AuthProvider } from './context/AuthContext';

// Layout Components
import MainLayout from './components/layout/MainLayout';
import ErrorBoundary from './components/common/ErrorBoundary';
import { Toast } from './components/common/Toast';

// Auth Components
import ProtectedRoute from './components/auth/ProtectedRoute';
import SessionTimeoutWarning from './components/auth/SessionTimeoutWarning';

// Auth Pages
import LoginPage from './pages/LoginPage';

// Feature Pages
import Dashboard from './pages/Dashboard';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';
import ClientsPage from './pages/ClientsPage';
import ClientDetailPage from './pages/ClientDetailPage';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (was cacheTime)
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

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
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />

              {/* Protected routes with layout */}
              <Route
                path="/*"
                element={
                  <ProtectedRoute>
                    <MainLayout>
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
                    </MainLayout>
                  </ProtectedRoute>
                }
              />
            </Routes>
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
