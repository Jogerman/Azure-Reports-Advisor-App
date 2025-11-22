import React from 'react';
import { Link } from 'react-router-dom';
import { FiMenu, FiX, FiCloud } from 'react-icons/fi';
import UserMenu from '../auth/UserMenu';
import DarkModeToggle from '../common/DarkModeToggle';

interface HeaderProps {
  onMenuClick: () => void;
  isSidebarOpen: boolean;
  user?: {
    name?: string;
    email: string;
    roles?: string[];
  } | null;
  onLogout: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick, isSidebarOpen, user, onLogout }) => {
  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40 shadow-sm transition-colors duration-200">
      <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        {/* Left section - Menu button and logo */}
        <div className="flex items-center space-x-4">
          {/* Mobile menu toggle */}
          <button
            onClick={onMenuClick}
            className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-azure-500 dark:focus:ring-azure-400 transition-colors lg:hidden"
            aria-label="Toggle sidebar"
          >
            {isSidebarOpen ? (
              <FiX className="h-6 w-6" />
            ) : (
              <FiMenu className="h-6 w-6" />
            )}
          </button>

          {/* Logo and brand */}
          <Link to="/dashboard" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 bg-gradient-to-br from-azure-500 to-azure-600 rounded-lg flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow">
              <FiCloud className="text-white w-5 h-5" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-lg font-bold text-gray-900 dark:text-white leading-tight transition-colors">
                Azure Advisor Reports
              </h1>
              <p className="text-xs text-gray-500 dark:text-gray-400 transition-colors">Professional Report Generation</p>
            </div>
          </Link>
        </div>

        {/* Right section - Navigation and user menu */}
        <div className="flex items-center space-x-2 sm:space-x-4">
          {/* Quick navigation - hidden on mobile */}
          <nav className="hidden md:flex items-center space-x-1">
            <Link
              to="/dashboard"
              className="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:text-azure-600 dark:hover:text-azure-400 hover:bg-azure-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Dashboard
            </Link>
            <Link
              to="/clients"
              className="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:text-azure-600 dark:hover:text-azure-400 hover:bg-azure-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Clients
            </Link>
            <Link
              to="/reports"
              className="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:text-azure-600 dark:hover:text-azure-400 hover:bg-azure-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Reports
            </Link>
          </nav>

          {/* Dark mode toggle */}
          <DarkModeToggle />

          {/* User menu */}
          {user && <UserMenu user={user} onLogout={onLogout} />}
        </div>
      </div>
    </header>
  );
};

export default Header;