import React, { useState } from 'react';
import { FiEye, FiEyeOff, FiAlertCircle, FiCheckCircle } from 'react-icons/fi';
import { azureSubscriptionApi } from '../../services/azureIntegrationApi';
import { AzureSubscriptionCreate, AzureSubscriptionUpdate, AzureSubscription } from '../../types/azureIntegration';
import ConnectionTestButton from './ConnectionTestButton';

interface AzureSubscriptionFormProps {
  subscription?: AzureSubscription;
  onSubmit: (data: AzureSubscriptionCreate | AzureSubscriptionUpdate) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
}

const AzureSubscriptionForm: React.FC<AzureSubscriptionFormProps> = ({
  subscription,
  onSubmit,
  onCancel,
  isSubmitting = false,
}) => {
  const isEditMode = !!subscription;

  const [formData, setFormData] = useState({
    name: subscription?.name || '',
    subscription_id: subscription?.subscription_id || '',
    tenant_id: subscription?.tenant_id || '',
    azure_client_id: subscription?.azure_client_id || '',
    client_secret: '',
    is_active: subscription?.is_active ?? true,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showSecret, setShowSecret] = useState(false);
  const [testConnectionAvailable, setTestConnectionAvailable] = useState(isEditMode);
  const [savedSubscriptionId, setSavedSubscriptionId] = useState(subscription?.id || '');

  // UUID validation regex
  const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

  const validateField = (name: string, value: string): string => {
    switch (name) {
      case 'name':
        return value.trim() ? '' : 'Name is required';
      case 'subscription_id':
      case 'tenant_id':
      case 'azure_client_id':
        if (!value.trim()) {
          return `${name.replace('_', ' ')} is required`;
        }
        if (!UUID_REGEX.test(value)) {
          return 'Must be a valid UUID format';
        }
        return '';
      case 'client_secret':
        if (!isEditMode && !value) {
          return 'Client secret is required';
        }
        if (value && value.length < 20) {
          return 'Client secret must be at least 20 characters';
        }
        return '';
      default:
        return '';
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    const fieldValue = type === 'checkbox' ? checked : value;

    setFormData(prev => ({
      ...prev,
      [name]: fieldValue,
    }));

    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    const error = validateField(name, value);
    if (error) {
      setErrors(prev => ({
        ...prev,
        [name]: error,
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    newErrors.name = validateField('name', formData.name);
    newErrors.subscription_id = validateField('subscription_id', formData.subscription_id);
    newErrors.tenant_id = validateField('tenant_id', formData.tenant_id);
    newErrors.azure_client_id = validateField('azure_client_id', formData.azure_client_id);

    if (!isEditMode || formData.client_secret) {
      newErrors.client_secret = validateField('client_secret', formData.client_secret);
    }

    // Remove empty errors
    Object.keys(newErrors).forEach(key => {
      if (!newErrors[key]) delete newErrors[key];
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const submitData: AzureSubscriptionCreate | AzureSubscriptionUpdate = isEditMode
      ? {
          name: formData.name,
          is_active: formData.is_active,
          ...(formData.client_secret && { client_secret: formData.client_secret }),
          ...(formData.tenant_id !== subscription?.tenant_id && { tenant_id: formData.tenant_id }),
          ...(formData.azure_client_id !== subscription?.azure_client_id && { azure_client_id: formData.azure_client_id }),
        }
      : formData;

    await onSubmit(submitData);
  };

  const isFormValid = () => {
    return (
      formData.name.trim() &&
      formData.subscription_id.trim() &&
      formData.tenant_id.trim() &&
      formData.azure_client_id.trim() &&
      (isEditMode || formData.client_secret.trim()) &&
      Object.keys(errors).length === 0
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Name */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
          Subscription Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={isSubmitting}
          className={`
            w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500
            ${errors.name ? 'border-red-300 bg-red-50' : 'border-gray-300'}
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
          placeholder="e.g., Production Subscription"
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
            <FiAlertCircle className="w-4 h-4" />
            {errors.name}
          </p>
        )}
        <p className="mt-1 text-xs text-gray-500">A friendly name to identify this subscription</p>
      </div>

      {/* Subscription ID */}
      <div>
        <label htmlFor="subscription_id" className="block text-sm font-medium text-gray-700 mb-1">
          Azure Subscription ID <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="subscription_id"
          name="subscription_id"
          value={formData.subscription_id}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={isSubmitting || isEditMode}
          className={`
            w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500 font-mono text-sm
            ${errors.subscription_id ? 'border-red-300 bg-red-50' : 'border-gray-300'}
            disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100
          `}
          placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        />
        {errors.subscription_id && (
          <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
            <FiAlertCircle className="w-4 h-4" />
            {errors.subscription_id}
          </p>
        )}
        {isEditMode && (
          <p className="mt-1 text-xs text-gray-500">Subscription ID cannot be changed</p>
        )}
      </div>

      {/* Tenant ID */}
      <div>
        <label htmlFor="tenant_id" className="block text-sm font-medium text-gray-700 mb-1">
          Azure Tenant ID <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="tenant_id"
          name="tenant_id"
          value={formData.tenant_id}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={isSubmitting}
          className={`
            w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500 font-mono text-sm
            ${errors.tenant_id ? 'border-red-300 bg-red-50' : 'border-gray-300'}
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
          placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        />
        {errors.tenant_id && (
          <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
            <FiAlertCircle className="w-4 h-4" />
            {errors.tenant_id}
          </p>
        )}
      </div>

      {/* Client ID */}
      <div>
        <label htmlFor="azure_client_id" className="block text-sm font-medium text-gray-700 mb-1">
          Application (Client) ID <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="azure_client_id"
          name="azure_client_id"
          value={formData.azure_client_id}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={isSubmitting}
          className={`
            w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500 font-mono text-sm
            ${errors.azure_client_id ? 'border-red-300 bg-red-50' : 'border-gray-300'}
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
          placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        />
        {errors.azure_client_id && (
          <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
            <FiAlertCircle className="w-4 h-4" />
            {errors.azure_client_id}
          </p>
        )}
      </div>

      {/* Client Secret */}
      <div>
        <label htmlFor="client_secret" className="block text-sm font-medium text-gray-700 mb-1">
          Client Secret {!isEditMode && <span className="text-red-500">*</span>}
        </label>
        <div className="relative">
          <input
            type={showSecret ? 'text' : 'password'}
            id="client_secret"
            name="client_secret"
            value={formData.client_secret}
            onChange={handleChange}
            onBlur={handleBlur}
            disabled={isSubmitting}
            className={`
              w-full px-3 py-2 pr-10 border rounded-lg focus:outline-none focus:ring-2 focus:ring-azure-500 font-mono text-sm
              ${errors.client_secret ? 'border-red-300 bg-red-50' : 'border-gray-300'}
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
            placeholder={isEditMode ? 'Leave blank to keep current secret' : 'Enter client secret'}
          />
          <button
            type="button"
            onClick={() => setShowSecret(!showSecret)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            aria-label={showSecret ? 'Hide secret' : 'Show secret'}
          >
            {showSecret ? <FiEyeOff className="w-5 h-5" /> : <FiEye className="w-5 h-5" />}
          </button>
        </div>
        {errors.client_secret && (
          <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
            <FiAlertCircle className="w-4 h-4" />
            {errors.client_secret}
          </p>
        )}
        {isEditMode && (
          <p className="mt-1 text-xs text-gray-500">Only provide if you want to update the secret</p>
        )}
      </div>

      {/* Is Active */}
      <div className="flex items-center">
        <input
          type="checkbox"
          id="is_active"
          name="is_active"
          checked={formData.is_active}
          onChange={handleChange}
          disabled={isSubmitting}
          className="w-4 h-4 text-azure-600 border-gray-300 rounded focus:ring-azure-500 disabled:opacity-50"
        />
        <label htmlFor="is_active" className="ml-2 text-sm font-medium text-gray-700">
          Active
        </label>
        <p className="ml-2 text-xs text-gray-500">
          (Inactive subscriptions will not sync automatically)
        </p>
      </div>

      {/* Test Connection - Only for edit mode */}
      {testConnectionAvailable && savedSubscriptionId && (
        <div className="pt-4 border-t border-gray-200">
          <ConnectionTestButton subscriptionId={savedSubscriptionId} />
        </div>
      )}

      {/* Form Actions */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-azure-500 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting || !isFormValid()}
          className="px-4 py-2 text-sm font-medium text-white bg-azure-600 rounded-lg hover:bg-azure-700 focus:outline-none focus:ring-2 focus:ring-azure-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Saving...' : isEditMode ? 'Update Subscription' : 'Add Subscription'}
        </button>
      </div>
    </form>
  );
};

export default AzureSubscriptionForm;
