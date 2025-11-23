import React, { useState, useEffect } from 'react';
import { FiCheckCircle, FiXCircle, FiLoader } from 'react-icons/fi';
import { azureSubscriptionApi } from '../../services/azureIntegrationApi';
import { ConnectionTestResult } from '../../types/azureIntegration';

interface ConnectionTestButtonProps {
  subscriptionId: string;
  onTestComplete?: (result: ConnectionTestResult) => void;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'secondary';
}

const ConnectionTestButton: React.FC<ConnectionTestButtonProps> = ({
  subscriptionId,
  onTestComplete,
  size = 'md',
  variant = 'secondary',
}) => {
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<ConnectionTestResult | null>(null);

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-2.5 text-base',
  };

  const variantStyles = {
    primary: 'bg-azure-600 hover:bg-azure-700 text-white',
    secondary: 'bg-white hover:bg-gray-50 text-gray-700 border border-gray-300',
  };

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (result) {
      timer = setTimeout(() => {
        setResult(null);
      }, 5000);
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [result]);

  const handleTest = async () => {
    setTesting(true);
    setResult(null);

    try {
      const testResult = await azureSubscriptionApi.testConnection(subscriptionId);
      setResult(testResult);
      if (onTestComplete) {
        onTestComplete(testResult);
      }
    } catch (error: any) {
      const errorResult: ConnectionTestResult = {
        success: false,
        subscription_id: subscriptionId,
        error_message: error.response?.data?.detail || error.message || 'Connection test failed',
      };
      setResult(errorResult);
      if (onTestComplete) {
        onTestComplete(errorResult);
      }
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="flex flex-col space-y-2">
      <button
        type="button"
        onClick={handleTest}
        disabled={testing}
        className={`
          inline-flex items-center justify-center gap-2 rounded-lg font-medium
          transition-colors focus:outline-none focus:ring-2 focus:ring-azure-500 focus:ring-offset-2
          disabled:opacity-50 disabled:cursor-not-allowed
          ${sizeStyles[size]}
          ${variantStyles[variant]}
        `}
        aria-busy={testing}
        aria-label="Test Azure connection"
      >
        {testing ? (
          <>
            <FiLoader className="w-4 h-4 animate-spin" />
            <span>Testing Connection...</span>
          </>
        ) : (
          <span>Test Connection</span>
        )}
      </button>

      {result && (
        <div
          className={`
            flex items-start gap-2 p-3 rounded-lg border text-sm
            ${result.success
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
            }
          `}
          role="alert"
          aria-live="polite"
        >
          {result.success ? (
            <FiCheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-green-600" />
          ) : (
            <FiXCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-600" />
          )}
          <div className="flex-1">
            <p className="font-medium">
              {result.success ? 'Connection Successful' : 'Connection Failed'}
            </p>
            {result.success && result.subscription_name && (
              <p className="mt-1">
                Connected to: <span className="font-semibold">{result.subscription_name}</span>
              </p>
            )}
            {!result.success && result.error_message && (
              <p className="mt-1">{result.error_message}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectionTestButton;
