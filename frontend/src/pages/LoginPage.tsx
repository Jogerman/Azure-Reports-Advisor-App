import React, { useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { FiLock, FiCheckCircle, FiCloud, FiShield, FiZap, FiTrendingUp } from 'react-icons/fi';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';

const LoginPage: React.FC = () => {
  const { isAuthenticated, isLoading, login } = useAuth();
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const location = useLocation();

  // Get the redirect location from state (if user was redirected to login)
  const from = (location.state as any)?.from?.pathname || '/';

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  if (isLoading) {
    return <LoadingSpinner fullScreen text="Initializing authentication..." />;
  }

  const handleLogin = async () => {
    setIsLoggingIn(true);
    try {
      await login();
    } finally {
      setIsLoggingIn(false);
    }
  };

  const features = [
    {
      icon: <FiZap className="w-5 h-5" />,
      title: 'Lightning Fast',
      description: 'Generate reports in minutes, not hours',
    },
    {
      icon: <FiShield className="w-5 h-5" />,
      title: 'Secure & Compliant',
      description: 'Enterprise-grade security with Azure AD',
    },
    {
      icon: <FiTrendingUp className="w-5 h-5" />,
      title: 'Professional Output',
      description: 'Client-ready reports with beautiful formatting',
    },
  ];

  const benefits = [
    'Generate professional Azure Advisor reports in minutes',
    'Manage multiple clients efficiently',
    'Track optimization recommendations',
    'Export reports in HTML and PDF formats',
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-azure-50 via-white to-azure-100 flex items-center justify-center px-4 sm:px-6 lg:px-8">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.1, 0.2, 0.1],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          className="absolute top-0 right-0 w-96 h-96 bg-azure-400 rounded-full blur-3xl"
        />
        <motion.div
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.1, 0.15, 0.1],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: 'easeInOut',
            delay: 1,
          }}
          className="absolute bottom-0 left-0 w-96 h-96 bg-azure-300 rounded-full blur-3xl"
        />
      </div>

      <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center relative z-10">
        {/* Left section - Branding and features */}
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center lg:text-left"
        >
          {/* Logo and title */}
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="flex items-center justify-center lg:justify-start space-x-3 mb-8"
          >
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
              className="w-14 h-14 bg-gradient-to-br from-azure-600 to-azure-700 rounded-xl flex items-center justify-center shadow-lg"
            >
              <FiCloud className="w-8 h-8 text-white" />
            </motion.div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Azure Advisor Reports
              </h1>
              <p className="text-sm text-gray-500">by Microsoft Azure</p>
            </div>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-4xl lg:text-5xl font-extrabold text-gray-900 mb-4 leading-tight"
          >
            Professional Report Generation Platform
          </motion.h2>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-xl text-gray-600 mb-8"
          >
            Transform Azure Advisor CSV exports into polished, client-ready reports in minutes.
          </motion.p>

          {/* Feature cards */}
          <div className="grid grid-cols-1 gap-4 mb-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.5 + index * 0.1 }}
                whileHover={{ scale: 1.02, x: 5 }}
                className="bg-white bg-opacity-50 backdrop-blur-sm rounded-xl p-4 shadow-sm border border-gray-100"
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-10 h-10 bg-azure-100 rounded-lg flex items-center justify-center text-azure-600">
                    {feature.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-gray-600">{feature.description}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Benefits list */}
          <div className="space-y-3 mb-8 hidden lg:block">
            {benefits.map((benefit, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.8 + index * 0.1 }}
                className="flex items-start space-x-3"
              >
                <FiCheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700 text-sm">{benefit}</span>
              </motion.div>
            ))}
          </div>

          {/* Security badge */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
            className="inline-flex items-center space-x-2 bg-white bg-opacity-70 backdrop-blur-sm text-azure-700 px-4 py-3 rounded-xl border border-azure-200 shadow-sm"
          >
            <FiLock className="w-4 h-4" />
            <span className="text-sm font-medium">
              Secured with Microsoft Azure Active Directory
            </span>
          </motion.div>
        </motion.div>

        {/* Right section - Login card */}
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="relative"
        >
          <motion.div
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.3 }}
            className="bg-white rounded-2xl shadow-2xl p-8 lg:p-12 relative overflow-hidden"
          >
            {/* Decorative gradient overlay */}
            <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-azure-500 via-azure-600 to-azure-500" />

            <div className="text-center mb-8">
              <motion.h3
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 }}
                className="text-3xl font-bold text-gray-900 mb-2"
              >
                Welcome Back
              </motion.h3>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="text-gray-600"
              >
                Sign in with your Microsoft account to continue
              </motion.p>
            </div>

            <AnimatePresence mode="wait">
              {isLoggingIn ? (
                <motion.div
                  key="logging-in"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="py-8"
                >
                  <LoadingSpinner size="lg" text="Signing you in..." />
                </motion.div>
              ) : (
                <motion.div
                  key="login-button"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <Button
                    variant="primary"
                    size="lg"
                    fullWidth
                    onClick={handleLogin}
                    icon={<FiCloud className="w-5 h-5" />}
                    className="mb-6 shadow-lg hover:shadow-xl transition-shadow"
                    aria-label="Sign in with Microsoft"
                  >
                    Sign in with Microsoft
                  </Button>

                  <div className="text-center mb-6">
                    <div className="relative">
                      <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-gray-200" />
                      </div>
                      <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-white text-gray-500">or</span>
                      </div>
                    </div>
                  </div>

                  <div className="text-center space-y-4">
                    <p className="text-sm text-gray-600">
                      Don't have an account?{' '}
                      <a
                        href="#"
                        className="text-azure-600 hover:text-azure-700 font-medium"
                        onClick={(e) => {
                          e.preventDefault();
                          // In production, this would link to registration or contact page
                        }}
                      >
                        Contact your administrator
                      </a>
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1 }}
              className="text-center mt-8 pt-6 border-t border-gray-100"
            >
              <p className="text-xs text-gray-500 leading-relaxed">
                By signing in, you agree to our{' '}
                <a href="#" className="text-azure-600 hover:text-azure-700 underline">
                  Terms of Service
                </a>{' '}
                and{' '}
                <a href="#" className="text-azure-600 hover:text-azure-700 underline">
                  Privacy Policy
                </a>
              </p>
            </motion.div>

            {/* Decorative elements */}
            <div className="absolute -top-4 -right-4 w-32 h-32 bg-azure-200 rounded-full opacity-20 blur-3xl pointer-events-none" />
            <div className="absolute -bottom-4 -left-4 w-40 h-40 bg-azure-300 rounded-full opacity-20 blur-3xl pointer-events-none" />
          </motion.div>

          {/* Floating badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2 }}
            className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 bg-white rounded-full shadow-lg px-6 py-3 flex items-center space-x-2 border border-gray-100"
          >
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-gray-700">All systems operational</span>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
};

export default LoginPage;