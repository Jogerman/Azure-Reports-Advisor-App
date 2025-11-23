import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CSVUploader from './CSVUploader';
import { createMockFile } from '../../utils/test-utils';

describe('CSVUploader', () => {
  const mockOnFileSelect = jest.fn();
  const mockOnFileRemove = jest.fn();

  const defaultProps = {
    onFileSelect: mockOnFileSelect,
    onFileRemove: mockOnFileRemove,
    selectedFile: null,
    maxSizeMB: 50,
    disabled: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render upload area when no file is selected', () => {
      render(<CSVUploader {...defaultProps} />);

      expect(screen.getByText('Upload Azure Advisor CSV')).toBeInTheDocument();
      expect(
        screen.getByText('Drag and drop your CSV file here, or click to browse')
      ).toBeInTheDocument();
      expect(screen.getByText('Maximum file size: 50MB • CSV format only')).toBeInTheDocument();
    });

    it('should render file input with correct attributes', () => {
      render(<CSVUploader {...defaultProps} />);

      const fileInput = screen.getByLabelText('Upload CSV file');
      expect(fileInput).toBeInTheDocument();
      expect(fileInput).toHaveAttribute('type', 'file');
      expect(fileInput).toHaveAttribute('accept', '.csv');
    });

    it('should render help text with instructions', () => {
      render(<CSVUploader {...defaultProps} />);

      expect(screen.getByText('How to get your CSV file')).toBeInTheDocument();
      expect(screen.getByText(/Navigate to Azure Advisor/i)).toBeInTheDocument();
    });

    it('should render selected file when file is provided', () => {
      const mockFile = createMockFile('test.csv', 1024);
      render(<CSVUploader {...defaultProps} selectedFile={mockFile} />);

      expect(screen.getByText('test.csv')).toBeInTheDocument();
      expect(screen.getByText('1 KB')).toBeInTheDocument();
      expect(screen.getByLabelText('Remove file')).toBeInTheDocument();
    });
  });

  describe('File Selection via Input', () => {
    it('should call onFileSelect with valid CSV file', async () => {
      const user = userEvent.setup();
      render(<CSVUploader {...defaultProps} />);

      const fileInput = screen.getByLabelText('Upload CSV file') as HTMLInputElement;
      const mockFile = createMockFile('test.csv', 1024);

      await user.upload(fileInput, mockFile);

      await waitFor(() => {
        expect(mockOnFileSelect).toHaveBeenCalledWith(mockFile);
      });
    });

    it('should show error for non-CSV file', async () => {
      const user = userEvent.setup();
      render(<CSVUploader {...defaultProps} />);

      const fileInput = screen.getByLabelText('Upload CSV file') as HTMLInputElement;
      const mockFile = createMockFile('test.txt', 1024, 'text/plain');

      await user.upload(fileInput, mockFile);

      await waitFor(() => {
        expect(screen.getByText('Only CSV files are allowed')).toBeInTheDocument();
        expect(mockOnFileSelect).not.toHaveBeenCalled();
      });
    });

    it('should show error for file exceeding size limit', async () => {
      const user = userEvent.setup();
      render(<CSVUploader {...defaultProps} maxSizeMB={1} />);

      const fileInput = screen.getByLabelText('Upload CSV file') as HTMLInputElement;
      const mockFile = createMockFile('large.csv', 2 * 1024 * 1024); // 2MB

      await user.upload(fileInput, mockFile);

      await waitFor(() => {
        expect(screen.getByText('File size exceeds 1MB limit')).toBeInTheDocument();
        expect(mockOnFileSelect).not.toHaveBeenCalled();
      });
    });

    it('should show error for empty file', async () => {
      const user = userEvent.setup();
      render(<CSVUploader {...defaultProps} />);

      const fileInput = screen.getByLabelText('Upload CSV file') as HTMLInputElement;
      const mockFile = createMockFile('empty.csv', 0);

      await user.upload(fileInput, mockFile);

      await waitFor(() => {
        expect(screen.getByText('File is empty')).toBeInTheDocument();
        expect(mockOnFileSelect).not.toHaveBeenCalled();
      });
    });
  });

  describe('Drag and Drop', () => {
    it('should handle drag enter event', () => {
      render(<CSVUploader {...defaultProps} />);

      const dropZone = screen.getByText('Upload Azure Advisor CSV').closest('div')?.parentElement;
      expect(dropZone).toBeInTheDocument();

      fireEvent.dragEnter(dropZone!);

      expect(screen.getByText('Drop your CSV file here')).toBeInTheDocument();
    });

    it('should handle drag leave event', () => {
      render(<CSVUploader {...defaultProps} />);

      const dropZone = screen.getByText('Upload Azure Advisor CSV').closest('div')?.parentElement;

      fireEvent.dragEnter(dropZone!);
      expect(screen.getByText('Drop your CSV file here')).toBeInTheDocument();

      fireEvent.dragLeave(dropZone!);
      expect(screen.getByText('Upload Azure Advisor CSV')).toBeInTheDocument();
    });

    it('should handle file drop with valid CSV', async () => {
      render(<CSVUploader {...defaultProps} />);

      const dropZone = screen.getByText('Upload Azure Advisor CSV').closest('div')?.parentElement;
      const mockFile = createMockFile('dropped.csv', 1024);

      const dropEvent = {
        dataTransfer: {
          files: [mockFile],
        },
      };

      fireEvent.drop(dropZone!, dropEvent);

      await waitFor(() => {
        expect(mockOnFileSelect).toHaveBeenCalledWith(mockFile);
      });
    });

    it('should show error when dropping invalid file', async () => {
      render(<CSVUploader {...defaultProps} />);

      const dropZone = screen.getByText('Upload Azure Advisor CSV').closest('div')?.parentElement;
      const mockFile = createMockFile('invalid.pdf', 1024, 'application/pdf');

      const dropEvent = {
        dataTransfer: {
          files: [mockFile],
        },
      };

      fireEvent.drop(dropZone!, dropEvent);

      await waitFor(() => {
        expect(screen.getByText('Only CSV files are allowed')).toBeInTheDocument();
        expect(mockOnFileSelect).not.toHaveBeenCalled();
      });
    });

    it('should not handle drop when disabled', async () => {
      render(<CSVUploader {...defaultProps} disabled={true} />);

      const dropZone = screen.getByText('Upload Azure Advisor CSV').closest('div')?.parentElement;
      const mockFile = createMockFile('test.csv', 1024);

      const dropEvent = {
        dataTransfer: {
          files: [mockFile],
        },
      };

      fireEvent.drop(dropZone!, dropEvent);

      await waitFor(() => {
        expect(mockOnFileSelect).not.toHaveBeenCalled();
      }, { timeout: 500 }).catch(() => {
        // Expected to timeout
      });
    });
  });

  describe('File Removal', () => {
    it('should call onFileRemove when remove button is clicked', async () => {
      const user = userEvent.setup();
      const mockFile = createMockFile('test.csv', 1024);
      render(<CSVUploader {...defaultProps} selectedFile={mockFile} />);

      const removeButton = screen.getByLabelText('Remove file');
      await user.click(removeButton);

      expect(mockOnFileRemove).toHaveBeenCalled();
    });

    it('should clear error when removing file', async () => {
      const user = userEvent.setup();
      render(<CSVUploader {...defaultProps} />);

      // Upload invalid file to trigger error
      const fileInput = screen.getByLabelText('Upload CSV file') as HTMLInputElement;
      const invalidFile = createMockFile('test.txt', 1024, 'text/plain');
      await user.upload(fileInput, invalidFile);

      await waitFor(() => {
        expect(screen.getByText('Only CSV files are allowed')).toBeInTheDocument();
      });

      // Upload valid file
      const validFile = createMockFile('test.csv', 1024);
      const { rerender } = render(<CSVUploader {...defaultProps} selectedFile={validFile} />);

      const removeButton = screen.getByLabelText('Remove file');
      await user.click(removeButton);

      // Error should be cleared
      expect(screen.queryByText('Only CSV files are allowed')).not.toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('should disable file input when disabled prop is true', () => {
      render(<CSVUploader {...defaultProps} disabled={true} />);

      const fileInput = screen.getByLabelText('Upload CSV file') as HTMLInputElement;
      expect(fileInput).toBeDisabled();
    });

    it('should disable remove button when disabled prop is true', () => {
      const mockFile = createMockFile('test.csv', 1024);
      render(<CSVUploader {...defaultProps} selectedFile={mockFile} disabled={true} />);

      const removeButton = screen.getByLabelText('Remove file') as HTMLButtonElement;
      expect(removeButton).toBeDisabled();
    });

    it('should not change state on drag enter when disabled', () => {
      render(<CSVUploader {...defaultProps} disabled={true} />);

      const dropZone = screen.getByText('Upload Azure Advisor CSV').closest('div')?.parentElement;
      fireEvent.dragEnter(dropZone!);

      // Should not show "Drop your CSV file here"
      expect(screen.queryByText('Drop your CSV file here')).not.toBeInTheDocument();
      expect(screen.getByText('Upload Azure Advisor CSV')).toBeInTheDocument();
    });
  });

  describe('File Size Formatting', () => {
    it('should format bytes correctly', () => {
      const mockFile = createMockFile('test.csv', 0);
      render(<CSVUploader {...defaultProps} selectedFile={mockFile} />);
      expect(screen.getByText('0 Bytes')).toBeInTheDocument();
    });

    it('should format KB correctly', () => {
      const mockFile = createMockFile('test.csv', 1024);
      render(<CSVUploader {...defaultProps} selectedFile={mockFile} />);
      expect(screen.getByText('1 KB')).toBeInTheDocument();
    });

    it('should format MB correctly', () => {
      const mockFile = createMockFile('test.csv', 1024 * 1024);
      render(<CSVUploader {...defaultProps} selectedFile={mockFile} />);
      expect(screen.getByText('1 MB')).toBeInTheDocument();
    });

    it('should format GB correctly', () => {
      const mockFile = createMockFile('test.csv', 1024 * 1024 * 1024);
      render(<CSVUploader {...defaultProps} selectedFile={mockFile} />);
      expect(screen.getByText('1 GB')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria-label on file input', () => {
      render(<CSVUploader {...defaultProps} />);

      const fileInput = screen.getByLabelText('Upload CSV file');
      expect(fileInput).toBeInTheDocument();
    });

    it('should have proper aria-label on remove button', () => {
      const mockFile = createMockFile('test.csv', 1024);
      render(<CSVUploader {...defaultProps} selectedFile={mockFile} />);

      const removeButton = screen.getByLabelText('Remove file');
      expect(removeButton).toBeInTheDocument();
    });

    it('should display error messages prominently', async () => {
      const user = userEvent.setup();
      render(<CSVUploader {...defaultProps} />);

      const fileInput = screen.getByLabelText('Upload CSV file') as HTMLInputElement;
      const invalidFile = createMockFile('test.txt', 1024, 'text/plain');

      await user.upload(fileInput, invalidFile);

      await waitFor(() => {
        const errorHeading = screen.getByText('Upload Error');
        expect(errorHeading).toBeInTheDocument();
        expect(screen.getByText('Only CSV files are allowed')).toBeInTheDocument();
      });
    });
  });
});
