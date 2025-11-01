import React, { useState, useCallback, DragEvent, ChangeEvent } from 'react';
import { FiUploadCloud, FiFile, FiX, FiAlertCircle, FiCheckCircle } from 'react-icons/fi';

interface CSVUploaderProps {
  onFileSelect: (file: File) => void;
  onFileRemove: () => void;
  selectedFile: File | null;
  maxSizeMB?: number;
  disabled?: boolean;
}

const CSVUploader: React.FC<CSVUploaderProps> = ({
  onFileSelect,
  onFileRemove,
  selectedFile,
  maxSizeMB = 50,
  disabled = false,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const maxSizeBytes = maxSizeMB * 1024 * 1024;

  const validateFile = (file: File): string | null => {
    // Check file type
    if (!file.name.toLowerCase().endsWith('.csv')) {
      return 'Only CSV files are allowed';
    }

    // Check file size
    if (file.size > maxSizeBytes) {
      return `File size exceeds ${maxSizeMB}MB limit`;
    }

    // Check if file is empty
    if (file.size === 0) {
      return 'File is empty';
    }

    return null;
  };

  const handleFile = useCallback((file: File) => {
    const validationError = validateFile(file);

    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    onFileSelect(file);
  }, [onFileSelect, maxSizeBytes]);

  const handleDragEnter = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragging(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFile(files[0]);
    }
  }, [disabled, handleFile]);

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleRemove = () => {
    setError(null);
    onFileRemove();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      {!selectedFile ? (
        <div
          className={`
            relative border-2 border-dashed rounded-lg transition-all
            ${isDragging
              ? 'border-azure-500 bg-azure-50'
              : 'border-gray-300 hover:border-azure-400'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".csv"
            onChange={handleFileInput}
            disabled={disabled}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
            aria-label="Upload CSV file"
          />

          <div className="p-8 text-center">
            <div className={`
              w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center
              ${isDragging ? 'bg-azure-100' : 'bg-gray-100'}
            `}>
              <FiUploadCloud className={`
                w-8 h-8
                ${isDragging ? 'text-azure-600' : 'text-gray-400'}
              `} />
            </div>

            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {isDragging ? 'Drop your CSV file here' : 'Upload Azure Advisor CSV'}
            </h3>

            <p className="text-sm text-gray-600 mb-4">
              Drag and drop your CSV file here, or click to browse
            </p>

            <p className="text-xs text-gray-500">
              Maximum file size: {maxSizeMB}MB • CSV format only
            </p>
          </div>
        </div>
      ) : (
        /* Selected File Display */
        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3 flex-1">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <FiFile className="w-5 h-5 text-green-600" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <h4 className="text-sm font-medium text-gray-900 truncate">
                    {selectedFile.name}
                  </h4>
                  <FiCheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                </div>
                <p className="text-xs text-gray-600">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>

            <button
              onClick={handleRemove}
              disabled={disabled}
              className="ml-4 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Remove file"
            >
              <FiX className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-start space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg">
          <FiAlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800">Upload Error</p>
            <p className="text-sm text-red-600 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Help Text */}
      {!selectedFile && !error && (
        <div className="bg-azure-50 border border-azure-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <FiAlertCircle className="w-5 h-5 text-azure-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-azure-900">How to get your CSV file</p>
              <ol className="text-sm text-azure-700 mt-2 space-y-1 ml-4 list-decimal">
                <li>Navigate to Azure Advisor in your Azure Portal</li>
                <li>Click on "Download" or "Export" to get recommendations</li>
                <li>Select CSV format and download the file</li>
                <li>Upload the CSV file here to generate your report</li>
              </ol>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CSVUploader;
