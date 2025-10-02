import React from 'react';
import { ToastContainer, toast, ToastOptions } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FiCheckCircle, FiAlertCircle, FiInfo, FiAlertTriangle } from 'react-icons/fi';

// Custom toast component wrapper
export const Toast: React.FC = () => {
  return (
    <ToastContainer
      position="top-right"
      autoClose={5000}
      hideProgressBar={false}
      newestOnTop={true}
      closeOnClick
      rtl={false}
      pauseOnFocusLoss
      draggable
      pauseOnHover
      theme="light"
      className="mt-16"
    />
  );
};

// Custom toast notifications with icons
const defaultOptions: ToastOptions = {
  position: 'top-right',
  autoClose: 5000,
  hideProgressBar: false,
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
};

export const showToast = {
  success: (message: string, options?: ToastOptions) => {
    toast.success(
      <div className="flex items-center">
        <FiCheckCircle className="w-5 h-5 mr-2" />
        <span>{message}</span>
      </div>,
      { ...defaultOptions, ...options }
    );
  },

  error: (message: string, options?: ToastOptions) => {
    toast.error(
      <div className="flex items-center">
        <FiAlertCircle className="w-5 h-5 mr-2" />
        <span>{message}</span>
      </div>,
      { ...defaultOptions, ...options }
    );
  },

  warning: (message: string, options?: ToastOptions) => {
    toast.warning(
      <div className="flex items-center">
        <FiAlertTriangle className="w-5 h-5 mr-2" />
        <span>{message}</span>
      </div>,
      { ...defaultOptions, ...options }
    );
  },

  info: (message: string, options?: ToastOptions) => {
    toast.info(
      <div className="flex items-center">
        <FiInfo className="w-5 h-5 mr-2" />
        <span>{message}</span>
      </div>,
      { ...defaultOptions, ...options }
    );
  },
};

export default Toast;