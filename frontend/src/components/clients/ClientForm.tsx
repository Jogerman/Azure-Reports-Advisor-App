import React from 'react';
import { Formik, Form, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import { useMutation } from '@tanstack/react-query';
import { clientService, Client, CreateClientData } from '../../services';
import { Button, showToast } from '../common';

interface ClientFormProps {
  client?: Client;
  onSuccess: () => void;
  onCancel: () => void;
}

// Validation schema
const clientSchema = Yup.object().shape({
  company_name: Yup.string()
    .required('Company name is required')
    .min(2, 'Company name must be at least 2 characters')
    .max(255, 'Company name must not exceed 255 characters'),
  industry: Yup.string()
    .max(100, 'Industry must not exceed 100 characters'),
  contact_email: Yup.string()
    .email('Invalid email address'),
  contact_phone: Yup.string()
    .max(50, 'Phone number must not exceed 50 characters'),
  azure_subscription_ids: Yup.string(),
  notes: Yup.string(),
  status: Yup.string()
    .oneOf(['active', 'inactive'], 'Invalid status'),
});

// Industry options - must match backend choices (lowercase)
const industries = [
  { value: 'technology', label: 'Technology' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'finance', label: 'Finance' },
  { value: 'education', label: 'Education' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'retail', label: 'Retail' },
  { value: 'government', label: 'Government' },
  { value: 'consulting', label: 'Consulting' },
  { value: 'other', label: 'Other' },
];

const ClientForm: React.FC<ClientFormProps> = ({ client, onSuccess, onCancel }) => {
  const [logoPreview, setLogoPreview] = React.useState<string | null>(
    client?.logo || null
  );
  const [selectedLogo, setSelectedLogo] = React.useState<File | null>(null);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: CreateClientData) => clientService.createClient(data),
    onSuccess: () => {
      showToast.success('Client created successfully');
      onSuccess();
    },
    onError: () => {
      showToast.error('Failed to create client');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      clientService.updateClient(id, data),
    onSuccess: () => {
      showToast.success('Client updated successfully');
      onSuccess();
    },
    onError: () => {
      showToast.error('Failed to update client');
    },
  });

  // Initial values
  const initialValues = {
    company_name: client?.company_name || '',
    industry: client?.industry || '',
    contact_email: client?.contact_email || '',
    contact_phone: client?.contact_phone || '',
    azure_subscription_ids: client?.azure_subscription_ids?.join('\n') || '',
    notes: client?.notes || '',
    status: client?.status || 'active',
  };

  const handleLogoChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        showToast.error('Please select a valid image file');
        return;
      }

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        showToast.error('Logo file size must be less than 5MB');
        return;
      }

      setSelectedLogo(file);

      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setLogoPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveLogo = () => {
    setSelectedLogo(null);
    setLogoPreview(null);
  };

  const handleSubmit = (values: any) => {
    // Parse subscription IDs from textarea
    const subscriptionIds = values.azure_subscription_ids
      .split('\n')
      .map((id: string) => id.trim())
      .filter((id: string) => id.length > 0);

    const data = {
      company_name: values.company_name,
      industry: values.industry || undefined,
      contact_email: values.contact_email || undefined,
      contact_phone: values.contact_phone || undefined,
      logo: selectedLogo || undefined,
      azure_subscription_ids: subscriptionIds,
      notes: values.notes || undefined,
      status: values.status,
    };

    if (client) {
      updateMutation.mutate({ id: client.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={clientSchema}
      onSubmit={handleSubmit}
    >
      {({ errors, touched }) => (
        <Form className="space-y-6">
          {/* Company Name */}
          <div>
            <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-1">
              Company Name <span className="text-red-500">*</span>
            </label>
            <Field
              type="text"
              id="company_name"
              name="company_name"
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent ${
                errors.company_name && touched.company_name
                  ? 'border-red-500'
                  : 'border-gray-300'
              }`}
              placeholder="Enter company name"
            />
            <ErrorMessage
              name="company_name"
              component="div"
              className="text-red-500 text-sm mt-1"
            />
          </div>

          {/* Industry */}
          <div>
            <label htmlFor="industry" className="block text-sm font-medium text-gray-700 mb-1">
              Industry
            </label>
            <Field
              as="select"
              id="industry"
              name="industry"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent"
            >
              <option value="">Select industry</option>
              {industries.map((industry) => (
                <option key={industry.value} value={industry.value}>
                  {industry.label}
                </option>
              ))}
            </Field>
            <ErrorMessage
              name="industry"
              component="div"
              className="text-red-500 text-sm mt-1"
            />
          </div>

          {/* Company Logo */}
          <div>
            <label htmlFor="logo" className="block text-sm font-medium text-gray-700 mb-1">
              Company Logo
            </label>
            <div className="space-y-3">
              {logoPreview && (
                <div className="relative inline-block">
                  <img
                    src={logoPreview}
                    alt="Logo preview"
                    className="h-24 w-24 object-contain border border-gray-300 rounded-lg p-2 bg-white"
                  />
                  <button
                    type="button"
                    onClick={handleRemoveLogo}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
                    title="Remove logo"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              )}
              <input
                type="file"
                id="logo"
                name="logo"
                accept="image/*"
                onChange={handleLogoChange}
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-lg file:border-0
                  file:text-sm file:font-semibold
                  file:bg-azure-50 file:text-azure-700
                  hover:file:bg-azure-100
                  cursor-pointer"
              />
              <p className="text-xs text-gray-500">
                Upload a company logo (PNG, JPG, GIF). Max size: 5MB. This logo will be used in generated reports.
              </p>
            </div>
          </div>

          {/* Contact Email */}
          <div>
            <label htmlFor="contact_email" className="block text-sm font-medium text-gray-700 mb-1">
              Contact Email
            </label>
            <Field
              type="email"
              id="contact_email"
              name="contact_email"
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent ${
                errors.contact_email && touched.contact_email
                  ? 'border-red-500'
                  : 'border-gray-300'
              }`}
              placeholder="contact@company.com"
            />
            <ErrorMessage
              name="contact_email"
              component="div"
              className="text-red-500 text-sm mt-1"
            />
          </div>

          {/* Contact Phone */}
          <div>
            <label htmlFor="contact_phone" className="block text-sm font-medium text-gray-700 mb-1">
              Contact Phone
            </label>
            <Field
              type="tel"
              id="contact_phone"
              name="contact_phone"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent"
              placeholder="+1 (555) 123-4567"
            />
            <ErrorMessage
              name="contact_phone"
              component="div"
              className="text-red-500 text-sm mt-1"
            />
          </div>

          {/* Azure Subscription IDs */}
          <div>
            <label htmlFor="azure_subscription_ids" className="block text-sm font-medium text-gray-700 mb-1">
              Azure Subscription IDs
            </label>
            <Field
              as="textarea"
              id="azure_subscription_ids"
              name="azure_subscription_ids"
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent"
              placeholder="Enter one subscription ID per line"
            />
            <p className="text-xs text-gray-500 mt-1">
              Enter one subscription ID per line
            </p>
            <ErrorMessage
              name="azure_subscription_ids"
              component="div"
              className="text-red-500 text-sm mt-1"
            />
          </div>

          {/* Notes */}
          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <Field
              as="textarea"
              id="notes"
              name="notes"
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent"
              placeholder="Add any additional notes..."
            />
            <ErrorMessage
              name="notes"
              component="div"
              className="text-red-500 text-sm mt-1"
            />
          </div>

          {/* Status (only show when editing) */}
          {client && (
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <Field
                as="select"
                id="status"
                name="status"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent"
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </Field>
              <ErrorMessage
                name="status"
                component="div"
                className="text-red-500 text-sm mt-1"
              />
            </div>
          )}

          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={isSubmitting}
            >
              {client ? 'Update Client' : 'Create Client'}
            </Button>
          </div>
        </Form>
      )}
    </Formik>
  );
};

export default ClientForm;