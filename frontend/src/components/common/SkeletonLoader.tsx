import React from 'react';
import { motion } from 'framer-motion';

interface SkeletonLoaderProps {
  variant?: 'text' | 'circular' | 'rectangular' | 'card';
  width?: string;
  height?: string;
  className?: string;
}

const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  variant = 'rectangular',
  width = '100%',
  height,
  className = '',
}) => {
  const getHeightClass = () => {
    if (height) return '';

    switch (variant) {
      case 'text':
        return 'h-4';
      case 'circular':
        return 'h-12 w-12';
      case 'card':
        return 'h-48';
      default:
        return 'h-32';
    }
  };

  const getShapeClass = () => {
    switch (variant) {
      case 'text':
        return 'rounded';
      case 'circular':
        return 'rounded-full';
      default:
        return 'rounded-lg';
    }
  };

  const style: React.CSSProperties = {
    width: variant === 'circular' ? height || '48px' : width,
    height: height || undefined,
  };

  return (
    <motion.div
      className={`bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 ${getHeightClass()} ${getShapeClass()} ${className}`}
      style={{
        ...style,
        backgroundSize: '200% 100%',
      }}
      animate={{
        backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: 'linear',
      }}
      role="status"
      aria-busy="true"
      aria-label="Loading"
    />
  );
};

// Composite skeleton components for common patterns
export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`bg-white rounded-lg shadow p-6 ${className}`} role="status" aria-busy="true" aria-label="Loading card">
    <div className="space-y-4">
      <SkeletonLoader variant="text" width="60%" />
      <SkeletonLoader variant="text" width="100%" />
      <SkeletonLoader variant="text" width="80%" />
      <div className="pt-4">
        <SkeletonLoader variant="rectangular" height="120px" />
      </div>
    </div>
  </div>
);

export const SkeletonTable: React.FC<{ rows?: number; className?: string }> = ({
  rows = 5,
  className = '',
}) => (
  <div className={`space-y-3 ${className}`} role="status" aria-busy="true" aria-label="Loading table">
    <div className="flex space-x-4">
      {[1, 2, 3, 4].map((i) => (
        <SkeletonLoader key={i} variant="text" width="25%" />
      ))}
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex space-x-4">
        {[1, 2, 3, 4].map((j) => (
          <SkeletonLoader key={j} variant="text" width="25%" height="40px" />
        ))}
      </div>
    ))}
  </div>
);

export const SkeletonList: React.FC<{ items?: number; className?: string }> = ({
  items = 5,
  className = '',
}) => (
  <div className={`space-y-4 ${className}`} role="status" aria-busy="true" aria-label="Loading list">
    {Array.from({ length: items }).map((_, i) => (
      <div key={i} className="flex items-center space-x-4">
        <SkeletonLoader variant="circular" />
        <div className="flex-1 space-y-2">
          <SkeletonLoader variant="text" width="40%" />
          <SkeletonLoader variant="text" width="60%" />
        </div>
      </div>
    ))}
  </div>
);

export default SkeletonLoader;
