import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiAlertCircle, FiArrowLeft, FiHome } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import LoadingSpinner from '../common/LoadingSpinner';
import Button from '../common/Button';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRoles }) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  // Announce route changes to screen readers
  useEffect(() => {
    const pageTitle = document.title;
    const announcement = `Navigated to ${pageTitle}`;

    // Create and announce to screen readers
    const ariaLive = document.createElement('div');
    ariaLive.setAttribute('role', 'status');
    ariaLive.setAttribute('aria-live', 'polite');
    ariaLive.setAttribute('aria-atomic', 'true');
    ariaLive.className = 'sr-only';
    ariaLive.textContent = announcement;
    document.body.appendChild(ariaLive);

    setTimeout(() => {
      document.body.removeChild(ariaLive);
    }, 1000);
  }, [location.pathname]);

  if (isLoading) {
    return (
      <div role="alert" aria-busy="true" aria-live="polite">
        <LoadingSpinner fullScreen text="Verifying authentication..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login page but save the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role-based access if required
  if (requiredRoles && requiredRoles.length > 0) {
    const hasRequiredRole = user?.roles?.some((role) =>
      requiredRoles.includes(role)
    );

    if (!hasRequiredRole) {
      return (
        <div
          className="min-h-screen flex items-center justify-center bg-gray-50 px-4"
          role="alert"
          aria-labelledby="access-denied-title"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="max-w-md w-full bg-white rounded-lg shadow-lg p-8"
          >
            <div className="text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.1, type: 'spring' }}
                className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4"
              >
                <FiAlertCircle className="w-8 h-8 text-red-600" aria-hidden="true" />
              </motion.div>

              <h1
                id="access-denied-title"
                className="text-2xl font-bold text-gray-900 mb-2"
              >
                Access Denied
              </h1>

              <p className="text-gray-600 mb-6">
                You don't have permission to access this page. The required role is:{' '}
                <span className="font-semibold">{requiredRoles.join(', ')}</span>.
              </p>

              <p className="text-sm text-gray-500 mb-8">
                Please contact your administrator if you believe this is an error.
              </p>

              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button
                  variant="secondary"
                  onClick={() => window.history.back()}
                  icon={<FiArrowLeft className="w-4 h-4" />}
                  aria-label="Go back to previous page"
                >
                  Go Back
                </Button>
                <Button
                  variant="primary"
                  onClick={() => (window.location.href = '/')}
                  icon={<FiHome className="w-4 h-4" />}
                  aria-label="Return to home page"
                >
                  Home
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      );
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;