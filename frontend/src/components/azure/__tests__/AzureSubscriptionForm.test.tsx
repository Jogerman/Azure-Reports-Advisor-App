import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AzureSubscriptionForm from '../AzureSubscriptionForm';

describe('AzureSubscriptionForm', () => {
  const mockOnSubmit = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders form fields correctly', () => {
    render(
      <AzureSubscriptionForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByLabelText(/Subscription Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Azure Subscription ID/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Azure Tenant ID/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Application \(Client\) ID/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Client Secret/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Active/i)).toBeInTheDocument();
  });

  it('validates UUID format for subscription_id', async () => {
    const user = userEvent.setup();
    render(
      <AzureSubscriptionForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    const subscriptionIdInput = screen.getByLabelText(/Azure Subscription ID/i);

    await user.type(subscriptionIdInput, 'invalid-uuid');
    await user.tab();

    await waitFor(() => {
      expect(screen.getByText(/Must be a valid UUID format/i)).toBeInTheDocument();
    });
  });

  it('validates required fields', async () => {
    const user = userEvent.setup();
    render(
      <AzureSubscriptionForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    const submitButton = screen.getByRole('button', { name: /Add Subscription/i });

    // Submit button should be disabled when form is empty
    expect(submitButton).toBeDisabled();
  });

  it('validates client secret minimum length', async () => {
    const user = userEvent.setup();
    render(
      <AzureSubscriptionForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    const secretInput = screen.getByLabelText(/Client Secret/i);

    await user.type(secretInput, 'short');
    await user.tab();

    await waitFor(() => {
      expect(screen.getByText(/Client secret must be at least 20 characters/i)).toBeInTheDocument();
    });
  });

  it('toggles password visibility', async () => {
    const user = userEvent.setup();
    render(
      <AzureSubscriptionForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    const secretInput = screen.getByLabelText(/Client Secret/i) as HTMLInputElement;
    const toggleButton = screen.getByLabelText(/Show secret/i);

    expect(secretInput.type).toBe('password');

    await user.click(toggleButton);
    expect(secretInput.type).toBe('text');

    await user.click(toggleButton);
    expect(secretInput.type).toBe('password');
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <AzureSubscriptionForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    await user.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);

    render(
      <AzureSubscriptionForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    const validData = {
      name: 'Test Subscription',
      subscription_id: '12345678-1234-1234-1234-123456789012',
      tenant_id: '87654321-4321-4321-4321-210987654321',
      client_id: 'abcdef12-3456-7890-abcd-ef1234567890',
      client_secret: 'this-is-a-very-long-secret-key-with-more-than-20-chars',
    };

    await user.type(screen.getByLabelText(/Subscription Name/i), validData.name);
    await user.type(screen.getByLabelText(/Azure Subscription ID/i), validData.subscription_id);
    await user.type(screen.getByLabelText(/Azure Tenant ID/i), validData.tenant_id);
    await user.type(screen.getByLabelText(/Application \(Client\) ID/i), validData.client_id);
    await user.type(screen.getByLabelText(/Client Secret/i), validData.client_secret);

    const submitButton = screen.getByRole('button', { name: /Add Subscription/i });

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });

    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(expect.objectContaining({
        name: validData.name,
        subscription_id: validData.subscription_id,
        tenant_id: validData.tenant_id,
        client_id: validData.client_id,
        client_secret: validData.client_secret,
        is_active: true,
      }));
    });
  });

  it('pre-fills form in edit mode', () => {
    const existingSubscription = {
      id: '1',
      name: 'Existing Subscription',
      subscription_id: '12345678-1234-1234-1234-123456789012',
      tenant_id: '87654321-4321-4321-4321-210987654321',
      client_id: 'abcdef12-3456-7890-abcd-ef1234567890',
      is_active: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: {
        id: 'user1',
        username: 'testuser',
        full_name: 'Test User',
      },
      last_sync_at: null,
      sync_status: 'never_synced' as const,
      sync_error_message: '',
    };

    render(
      <AzureSubscriptionForm
        subscription={existingSubscription}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    expect((screen.getByLabelText(/Subscription Name/i) as HTMLInputElement).value).toBe(existingSubscription.name);
    expect((screen.getByLabelText(/Azure Subscription ID/i) as HTMLInputElement).value).toBe(existingSubscription.subscription_id);
    expect((screen.getByLabelText(/Azure Tenant ID/i) as HTMLInputElement).value).toBe(existingSubscription.tenant_id);
    expect((screen.getByLabelText(/Application \(Client\) ID/i) as HTMLInputElement).value).toBe(existingSubscription.client_id);
    expect((screen.getByLabelText(/Active/i) as HTMLInputElement).checked).toBe(false);
  });

  it('disables subscription_id field in edit mode', () => {
    const existingSubscription = {
      id: '1',
      name: 'Existing Subscription',
      subscription_id: '12345678-1234-1234-1234-123456789012',
      tenant_id: '87654321-4321-4321-4321-210987654321',
      client_id: 'abcdef12-3456-7890-abcd-ef1234567890',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      created_by: {
        id: 'user1',
        username: 'testuser',
        full_name: 'Test User',
      },
      last_sync_at: null,
      sync_status: 'never_synced' as const,
      sync_error_message: '',
    };

    render(
      <AzureSubscriptionForm
        subscription={existingSubscription}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    const subscriptionIdInput = screen.getByLabelText(/Azure Subscription ID/i);
    expect(subscriptionIdInput).toBeDisabled();
  });
});
