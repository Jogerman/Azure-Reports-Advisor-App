import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../utils/test-utils';
import Modal from './Modal';

describe('Modal Component', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    mockOnClose.mockClear();
  });

  afterEach(() => {
    // Reset body overflow
    document.body.style.overflow = 'unset';
  });

  // Test 1: Modal is hidden when isOpen is false
  it('does not render when isOpen is false', () => {
    render(
      <Modal isOpen={false} onClose={mockOnClose}>
        Modal Content
      </Modal>
    );
    expect(screen.queryByText('Modal Content')).not.toBeInTheDocument();
  });

  // Test 2: Modal is visible when isOpen is true
  it('renders when isOpen is true', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        Modal Content
      </Modal>
    );
    expect(screen.getByText('Modal Content')).toBeInTheDocument();
  });

  // Test 3: Title rendering
  it('renders title when provided', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
        Content
      </Modal>
    );
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
  });

  // Test 4: No title rendering
  it('does not render title when not provided', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={mockOnClose}>
        Content
      </Modal>
    );
    const header = container.querySelector('.border-b');
    expect(header).not.toBeInTheDocument();
  });

  // Test 5: Footer rendering
  it('renders footer when provided', () => {
    const footer = <button>Save</button>;
    render(
      <Modal isOpen={true} onClose={mockOnClose} footer={footer}>
        Content
      </Modal>
    );
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
  });

  // Test 6: No footer rendering
  it('does not render footer when not provided', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={mockOnClose}>
        Content
      </Modal>
    );
    const footer = container.querySelector('.border-t');
    expect(footer).not.toBeInTheDocument();
  });

  // Test 7: Close button click
  it('calls onClose when close button is clicked', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} title="Test">
        Content
      </Modal>
    );

    const closeButton = screen.getByLabelText('Close modal');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  // Test 8: Overlay click closes modal
  it('calls onClose when overlay is clicked by default', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={mockOnClose}>
        Content
      </Modal>
    );

    const overlay = container.querySelector('.fixed.inset-0') as HTMLElement;
    fireEvent.click(overlay);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  // Test 9: Overlay click disabled
  it('does not close when overlay is clicked if closeOnOverlayClick is false', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={mockOnClose} closeOnOverlayClick={false}>
        Content
      </Modal>
    );

    const overlay = container.querySelector('.fixed.inset-0') as HTMLElement;
    fireEvent.click(overlay);

    expect(mockOnClose).not.toHaveBeenCalled();
  });

  // Test 10: Modal content click doesn't close
  it('does not close when modal content is clicked', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        <div data-testid="modal-content">Content</div>
      </Modal>
    );

    const content = screen.getByTestId('modal-content');
    fireEvent.click(content);

    expect(mockOnClose).not.toHaveBeenCalled();
  });

  // Test 11: ESC key closes modal
  it('calls onClose when ESC key is pressed', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        Content
      </Modal>
    );

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  // Test 12: Other keys don't close modal
  it('does not close when other keys are pressed', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose}>
        Content
      </Modal>
    );

    fireEvent.keyDown(document, { key: 'Enter' });
    fireEvent.keyDown(document, { key: 'Space' });

    expect(mockOnClose).not.toHaveBeenCalled();
  });

  // Test 13: Body scroll prevention
  it('prevents body scroll when modal is open', async () => {
    const { rerender } = render(
      <Modal isOpen={false} onClose={mockOnClose}>
        Content
      </Modal>
    );

    // Modal sets overflow to 'unset' when closed
    expect(document.body.style.overflow).toBe('unset');

    rerender(
      <Modal isOpen={true} onClose={mockOnClose}>
        Content
      </Modal>
    );

    await waitFor(() => {
      expect(document.body.style.overflow).toBe('hidden');
    });
  });

  // Test 14: Body scroll restored
  it('restores body scroll when modal is closed', async () => {
    const { rerender, unmount } = render(
      <Modal isOpen={true} onClose={mockOnClose}>
        Content
      </Modal>
    );

    expect(document.body.style.overflow).toBe('hidden');

    rerender(
      <Modal isOpen={false} onClose={mockOnClose}>
        Content
      </Modal>
    );

    await waitFor(() => {
      expect(document.body.style.overflow).toBe('unset');
    });

    unmount();
    expect(document.body.style.overflow).toBe('unset');
  });

  // Test 15: Small size
  it('renders with small size', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={mockOnClose} size="sm">
        Content
      </Modal>
    );

    const modal = container.querySelector('.max-w-md');
    expect(modal).toBeInTheDocument();
  });

  // Test 16: Medium size (default)
  it('renders with medium size by default', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={mockOnClose}>
        Content
      </Modal>
    );

    const modal = container.querySelector('.max-w-lg');
    expect(modal).toBeInTheDocument();
  });

  // Test 17: Large size
  it('renders with large size', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={mockOnClose} size="lg">
        Content
      </Modal>
    );

    const modal = container.querySelector('.max-w-2xl');
    expect(modal).toBeInTheDocument();
  });

  // Test 18: Extra large size
  it('renders with extra large size', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={mockOnClose} size="xl">
        Content
      </Modal>
    );

    const modal = container.querySelector('.max-w-4xl');
    expect(modal).toBeInTheDocument();
  });

  // Test 19: Complex children
  it('renders complex children correctly', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} title="Form Modal">
        <form>
          <label htmlFor="name">Name</label>
          <input id="name" type="text" />
          <button type="submit">Submit</button>
        </form>
      </Modal>
    );

    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  // Test 20: Accessibility - ARIA label
  it('has proper ARIA label for close button', () => {
    render(
      <Modal isOpen={true} onClose={mockOnClose} title="Test">
        Content
      </Modal>
    );

    const closeButton = screen.getByLabelText('Close modal');
    expect(closeButton).toBeInTheDocument();
    expect(closeButton).toHaveAttribute('aria-label', 'Close modal');
  });
});
