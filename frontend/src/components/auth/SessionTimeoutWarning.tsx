import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiClock, FiAlertCircle } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import Button from '../common/Button';

interface SessionTimeoutWarningProps {
  warningTime?: number; // Minutes before expiration to show warning
  sessionDuration?: number; // Total session duration in minutes (default: 60)
}

const SessionTimeoutWarning: React.FC<SessionTimeoutWarningProps> = ({
  warningTime = 5, // Show warning 5 minutes before expiration
  sessionDuration = 60, // Azure AD default token expiration (60 minutes)
}) => {
  const { getAccessToken, login, isAuthenticated } = useAuth();
  const [showWarning, setShowWarning] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [tokenExpiryTime, setTokenExpiryTime] = useState<number | null>(null);

  // Calculate token expiry time
  useEffect(() => {
    if (!isAuthenticated) {
      setShowWarning(false);
      setTokenExpiryTime(null);
      return;
    }

    const checkTokenExpiry = async () => {
      try {
        const token = await getAccessToken();
        if (token) {
          // Decode JWT to get expiry time (basic parsing)
          const payload = JSON.parse(atob(token.split('.')[1]));
          const expiryTime = payload.exp * 1000; // Convert to milliseconds
          setTokenExpiryTime(expiryTime);
        }
      } catch (error) {
        console.error('Error checking token expiry:', error);
      }
    };

    checkTokenExpiry();

    // Recheck every minute
    const interval = setInterval(checkTokenExpiry, 60000);

    return () => clearInterval(interval);
  }, [isAuthenticated, getAccessToken]);

  // Check if warning should be shown
  useEffect(() => {
    if (!tokenExpiryTime) return;

    const checkWarning = () => {
      const now = Date.now();
      const timeLeft = tokenExpiryTime - now;
      const minutesLeft = Math.floor(timeLeft / 60000);

      setTimeRemaining(minutesLeft);

      if (minutesLeft <= warningTime && minutesLeft > 0) {
        setShowWarning(true);
      } else {
        setShowWarning(false);
      }
    };

    checkWarning();
    const interval = setInterval(checkWarning, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [tokenExpiryTime, warningTime]);

  const handleExtendSession = useCallback(async () => {
    try {
      // This will trigger a silent token refresh
      await getAccessToken();
      setShowWarning(false);
    } catch (error) {
      console.error('Error extending session:', error);
      // If silent refresh fails, prompt for interactive login
      await login();
    }
  }, [getAccessToken, login]);

  const handleDismiss = useCallback(() => {
    setShowWarning(false);
  }, []);

  if (!showWarning) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="fixed top-4 right-4 z-50 max-w-md"
      >
        <div className="bg-white rounded-lg shadow-2xl border-l-4 border-yellow-500 p-6">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                <FiClock className="w-5 h-5 text-yellow-600" />
              </div>
            </div>

            <div className="flex-1">
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-lg font-semibold text-gray-900">
                  Session Expiring Soon
                </h3>
                <button
                  onClick={handleDismiss}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                  aria-label="Dismiss warning"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="flex items-center space-x-2 mb-4">
                <FiAlertCircle className="w-4 h-4 text-yellow-600" />
                <p className="text-sm text-gray-600">
                  Your session will expire in{' '}
                  <span className="font-semibold text-yellow-700">
                    {timeRemaining} {timeRemaining === 1 ? 'minute' : 'minutes'}
                  </span>
                </p>
              </div>

              <p className="text-sm text-gray-600 mb-4">
                Click below to extend your session or your work may be lost.
              </p>

              <div className="flex space-x-3">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleExtendSession}
                  className="flex-1"
                >
                  Extend Session
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleDismiss}
                  className="flex-1"
                >
                  Dismiss
                </Button>
              </div>
            </div>
          </div>

          {/* Progress bar */}
          <motion.div
            className="mt-4 h-1 bg-gray-200 rounded-full overflow-hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <motion.div
              className="h-full bg-yellow-500"
              initial={{ width: '100%' }}
              animate={{ width: '0%' }}
              transition={{
                duration: timeRemaining * 60,
                ease: 'linear',
              }}
            />
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default SessionTimeoutWarning;
