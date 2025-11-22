import React from 'react';
import { FiSun, FiMoon } from 'react-icons/fi';
import { useDarkMode } from '../../context/DarkModeContext';

interface DarkModeToggleProps {
  className?: string;
}

const DarkModeToggle: React.FC<DarkModeToggleProps> = ({ className = '' }) => {
  const { isDarkMode, toggleDarkMode } = useDarkMode();

  return (
    <button
      onClick={toggleDarkMode}
      className={`
        relative p-2 rounded-lg
        text-gray-600 dark:text-gray-300
        hover:text-gray-900 dark:hover:text-white
        hover:bg-gray-100 dark:hover:bg-gray-700
        focus:outline-none focus:ring-2 focus:ring-azure-500 dark:focus:ring-azure-400
        transition-all duration-200 ease-in-out
        ${className}
      `}
      aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <div className="relative w-6 h-6">
        {/* Sun icon - visible in dark mode */}
        <FiSun
          className={`
            absolute inset-0 w-6 h-6
            transition-all duration-300 ease-in-out
            ${isDarkMode ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-90 scale-0'}
          `}
        />
        {/* Moon icon - visible in light mode */}
        <FiMoon
          className={`
            absolute inset-0 w-6 h-6
            transition-all duration-300 ease-in-out
            ${!isDarkMode ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 rotate-90 scale-0'}
          `}
        />
      </div>
    </button>
  );
};

export default DarkModeToggle;
