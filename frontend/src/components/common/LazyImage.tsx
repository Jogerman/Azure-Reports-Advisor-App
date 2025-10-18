import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
  placeholderSrc?: string;
  onLoad?: () => void;
  onError?: () => void;
}

/**
 * LazyImage Component
 *
 * Optimized image loading with:
 * - Native lazy loading (loading="lazy")
 * - Intersection Observer API for progressive loading
 * - Placeholder while loading
 * - Fade-in animation when loaded
 * - Error handling with fallback
 * - Async decoding for better performance
 */
export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  className = '',
  placeholderSrc = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect width="400" height="300" fill="%23e5e7eb"/%3E%3C/svg%3E',
  onLoad,
  onError,
}) => {
  const [imageSrc, setImageSrc] = useState<string>(placeholderSrc);
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    // Use Intersection Observer for better performance
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Image is visible, load it
            setImageSrc(src);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '50px', // Start loading 50px before image enters viewport
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, [src]);

  const handleLoad = () => {
    setIsLoaded(true);
    onLoad?.();
  };

  const handleError = () => {
    setHasError(true);
    setImageSrc(placeholderSrc);
    onError?.();
  };

  return (
    <motion.img
      ref={imgRef}
      src={imageSrc}
      alt={alt}
      className={className}
      loading="lazy"
      decoding="async"
      onLoad={handleLoad}
      onError={handleError}
      initial={{ opacity: 0 }}
      animate={{ opacity: isLoaded ? 1 : 0.5 }}
      transition={{ duration: 0.3 }}
      style={{
        backgroundColor: hasError ? '#f3f4f6' : 'transparent',
      }}
    />
  );
};

interface LazyBackgroundImageProps {
  src: string;
  className?: string;
  children?: React.ReactNode;
  fallbackColor?: string;
}

/**
 * LazyBackgroundImage Component
 *
 * Lazy-loaded background image with fade-in effect
 */
export const LazyBackgroundImage: React.FC<LazyBackgroundImageProps> = ({
  src,
  className = '',
  children,
  fallbackColor = '#e5e7eb',
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [backgroundImage, setBackgroundImage] = useState<string>('none');
  const divRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Preload image
            const img = new Image();
            img.src = src;
            img.onload = () => {
              setBackgroundImage(`url(${src})`);
              setIsLoaded(true);
            };
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '50px',
      }
    );

    if (divRef.current) {
      observer.observe(divRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, [src]);

  return (
    <motion.div
      ref={divRef}
      className={className}
      style={{
        backgroundImage,
        backgroundColor: fallbackColor,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
      initial={{ opacity: 0 }}
      animate={{ opacity: isLoaded ? 1 : 0.8 }}
      transition={{ duration: 0.5 }}
    >
      {children}
    </motion.div>
  );
};

export default LazyImage;
