import React from 'react';
import Modal from './Modal';
import Button from './Button';
import { FiAlertTriangle } from 'react-icons/fi';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  loading?: boolean;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
  loading = false,
}) => {
  const variantStyles: Record<string, { icon: React.ReactElement; bg: string; buttonVariant: 'danger' | 'primary' }> = {
    danger: {
      icon: <FiAlertTriangle className="w-6 h-6 text-red-600" /> as React.ReactElement,
      bg: 'bg-red-100',
      buttonVariant: 'danger' as const,
    },
    warning: {
      icon: <FiAlertTriangle className="w-6 h-6 text-yellow-600" /> as React.ReactElement,
      bg: 'bg-yellow-100',
      buttonVariant: 'primary' as const,
    },
    info: {
      icon: <FiAlertTriangle className="w-6 h-6 text-blue-600" /> as React.ReactElement,
      bg: 'bg-blue-100',
      buttonVariant: 'primary' as const,
    },
  };

  const style = variantStyles[variant];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="sm"
      closeOnOverlayClick={!loading}
    >
      <div className="text-center">
        <div className={`mx-auto flex items-center justify-center w-12 h-12 rounded-full ${style.bg}`}>
          {style.icon}
        </div>

        <h3 className="mt-4 text-lg font-medium text-gray-900">
          {title}
        </h3>

        <p className="mt-2 text-sm text-gray-600">
          {message}
        </p>

        <div className="mt-6 flex space-x-3">
          <Button
            variant="outline"
            fullWidth
            onClick={onClose}
            disabled={loading}
          >
            {cancelText}
          </Button>
          <Button
            variant={style.buttonVariant}
            fullWidth
            onClick={onConfirm}
            loading={loading}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default ConfirmDialog;