import React from 'react';
import { FiGithub, FiMail, FiHelpCircle } from 'react-icons/fi';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            {/* Left section - Copyright */}
            <div className="text-center md:text-left">
              <p className="text-sm text-gray-600">
                © {currentYear} Azure Advisor Reports Platform. All rights reserved.
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Powered by Microsoft Azure
              </p>
            </div>

            {/* Middle section - Links */}
            <div className="flex items-center space-x-6">
              <a
                href="/docs"
                className="text-sm text-gray-600 hover:text-azure-600 transition-colors"
              >
                Documentation
              </a>
              <a
                href="/support"
                className="text-sm text-gray-600 hover:text-azure-600 transition-colors"
              >
                Support
              </a>
              <a
                href="/privacy"
                className="text-sm text-gray-600 hover:text-azure-600 transition-colors"
              >
                Privacy
              </a>
              <a
                href="/terms"
                className="text-sm text-gray-600 hover:text-azure-600 transition-colors"
              >
                Terms
              </a>
            </div>

            {/* Right section - Social links */}
            <div className="flex items-center space-x-4">
              <a
                href="mailto:support@azureadvisor.com"
                className="p-2 text-gray-600 hover:text-azure-600 hover:bg-gray-100 rounded-md transition-colors"
                aria-label="Email support"
              >
                <FiMail className="h-5 w-5" />
              </a>
              <a
                href="/help"
                className="p-2 text-gray-600 hover:text-azure-600 hover:bg-gray-100 rounded-md transition-colors"
                aria-label="Help center"
              >
                <FiHelpCircle className="h-5 w-5" />
              </a>
              <a
                href="https://github.com/your-org/azure-advisor-reports"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 text-gray-600 hover:text-azure-600 hover:bg-gray-100 rounded-md transition-colors"
                aria-label="GitHub repository"
              >
                <FiGithub className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;