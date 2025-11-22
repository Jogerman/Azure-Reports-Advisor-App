import React, { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  FiHome,
  FiUsers,
  FiFileText,
  FiClock,
  FiSettings,
  FiBarChart2,
  FiHelpCircle,
} from 'react-icons/fi';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  userRoles?: string[];
}

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  onClick?: () => void;
  badge?: string | number;
  requiredRoles?: string[];
  userRoles?: string[];
}

const NavItem: React.FC<NavItemProps> = ({
  to,
  icon,
  label,
  onClick,
  badge,
  requiredRoles,
  userRoles = []
}) => {
  // Check role-based access
  if (requiredRoles && requiredRoles.length > 0) {
    const hasRequiredRole = userRoles.some(role => requiredRoles.includes(role));
    if (!hasRequiredRole) {
      return null;
    }
  }

  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center justify-between px-4 py-3 rounded-lg transition-all duration-200 group ${
          isActive
            ? 'bg-azure-50 dark:bg-azure-900/30 text-azure-700 dark:text-azure-400 font-medium shadow-sm'
            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
        }`
      }
    >
      <div className="flex items-center space-x-3">
        <span className="text-xl group-hover:scale-110 transition-transform" aria-hidden="true">{icon}</span>
        <span className="text-sm">{label}</span>
      </div>
      {badge && (
        <span className="inline-flex items-center justify-center px-2 py-0.5 text-xs font-medium rounded-full bg-azure-100 dark:bg-azure-900/50 text-azure-700 dark:text-azure-300">
          {badge}
        </span>
      )}
    </NavLink>
  );
};

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, userRoles = [] }) => {
  // Prevent body scroll when sidebar is open on mobile
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 z-20 lg:hidden transition-opacity"
          onClick={onClose}
          role="button"
          aria-label="Close navigation menu"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onClose();
            }
          }}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-30 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-all duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {/* Main Menu */}
            <div className="mb-4">
              <h2 className="px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                Main Menu
              </h2>
              <div className="space-y-1">
                <NavItem
                  to="/dashboard"
                  icon={<FiHome />}
                  label="Dashboard"
                  onClick={onClose}
                  userRoles={userRoles}
                />
                <NavItem
                  to="/clients"
                  icon={<FiUsers />}
                  label="Clients"
                  onClick={onClose}
                  userRoles={userRoles}
                />
                <NavItem
                  to="/reports"
                  icon={<FiFileText />}
                  label="Reports"
                  onClick={onClose}
                  userRoles={userRoles}
                />
                <NavItem
                  to="/history"
                  icon={<FiClock />}
                  label="History"
                  onClick={onClose}
                  userRoles={userRoles}
                />
              </div>
            </div>

            {/* Analytics & Insights */}
            <div className="pt-4 border-t border-gray-200 dark:border-gray-700 mb-4">
              <h2 className="px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                Analytics
              </h2>
              <div className="space-y-1">
                <NavItem
                  to="/analytics"
                  icon={<FiBarChart2 />}
                  label="Analytics"
                  onClick={onClose}
                  userRoles={userRoles}
                  requiredRoles={['admin', 'manager', 'analyst']}
                />
              </div>
            </div>

            {/* Settings */}
            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
              <h2 className="px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                Configuration
              </h2>
              <div className="space-y-1">
                <NavItem
                  to="/settings"
                  icon={<FiSettings />}
                  label="Settings"
                  onClick={onClose}
                  userRoles={userRoles}
                />
              </div>
            </div>
          </nav>

          {/* Help Section Footer */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="bg-gradient-to-br from-azure-50 to-azure-100 dark:from-azure-900/20 dark:to-azure-900/30 rounded-lg p-4 border border-azure-200 dark:border-azure-800">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-azure-600 dark:bg-azure-500 rounded-lg flex items-center justify-center flex-shrink-0" aria-hidden="true">
                  <FiHelpCircle className="w-5 h-5 text-white" aria-hidden="true" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-azure-900 dark:text-azure-100 mb-1">
                    Need Help?
                  </h3>
                  <p className="text-xs text-azure-700 dark:text-azure-300 mb-2">
                    Access guides, tutorials, and support resources.
                  </p>
                  <a
                    href="/docs"
                    className="inline-flex items-center text-xs font-medium text-azure-600 dark:text-azure-400 hover:text-azure-700 dark:hover:text-azure-300 transition-colors"
                  >
                    Documentation →
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;