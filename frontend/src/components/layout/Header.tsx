import React from 'react';
import { Link } from 'react-router-dom';
import { FiMenu, FiX, FiCloud } from 'react-icons/fi';
import UserMenu from '../auth/UserMenu';

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
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
      <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        {/* Left section - Menu button and logo */}
        <div className="flex items-center space-x-4">
          {/* Mobile menu toggle */}
          <button
            onClick={onMenuClick}
            className="p-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-azure-500 transition-colors lg:hidden"
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
              <h1 className="text-lg font-bold text-gray-900 leading-tight">
                Azure Advisor Reports
              </h1>
              <p className="text-xs text-gray-500">Professional Report Generation</p>
            </div>
          </Link>
        </div>

        {/* Right section - Navigation and user menu */}
        <div className="flex items-center space-x-4">
          {/* Quick navigation - hidden on mobile */}
          <nav className="hidden md:flex items-center space-x-1">
            <Link
              to="/dashboard"
              className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-azure-600 hover:bg-azure-50 rounded-lg transition-colors"
            >
              Dashboard
            </Link>
            <Link
              to="/clients"
              className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-azure-600 hover:bg-azure-50 rounded-lg transition-colors"
            >
              Clients
            </Link>
            <Link
              to="/reports"
              className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-azure-600 hover:bg-azure-50 rounded-lg transition-colors"
            >
              Reports
            </Link>
          </nav>

          {/* User menu */}
          {user && <UserMenu user={user} onLogout={onLogout} />}
        </div>
      </div>
    </header>
  );
};

export default Header;