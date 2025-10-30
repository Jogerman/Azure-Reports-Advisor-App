import React from 'react';

interface UserProfileProps {
  user: {
    id: string;
    name?: string;
    email: string;
    roles?: string[];
  };
  showRoles?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const UserProfile: React.FC<UserProfileProps> = ({
  user,
  showRoles = true,
  size = 'md'
}) => {
  const sizeClasses = {
    sm: {
      container: 'p-4',
      avatar: 'w-12 h-12',
      icon: 'w-6 h-6',
      name: 'text-sm',
      email: 'text-xs',
      role: 'text-xs',
    },
    md: {
      container: 'p-6',
      avatar: 'w-16 h-16',
      icon: 'w-8 h-8',
      name: 'text-lg',
      email: 'text-sm',
      role: 'text-sm',
    },
    lg: {
      container: 'p-8',
      avatar: 'w-24 h-24',
      icon: 'w-12 h-12',
      name: 'text-2xl',
      email: 'text-base',
      role: 'text-base',
    },
  };

  const classes = sizeClasses[size];

  // Get user initials for avatar
  const getInitials = (name?: string): string => {
    if (!name) {
      // Fallback to email initial if name is not available
      return user.email[0].toUpperCase();
    }
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase()
      .substring(0, 2);
  };

  // Get display name with fallback to email
  const getDisplayName = (): string => {
    return user.name || user.email.split('@')[0];
  };

  // Format roles for display
  const formatRole = (role: string): string => {
    return role
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${classes.container}`}>
      <div className="flex items-center space-x-4">
        {/* Avatar */}
        <div className={`${classes.avatar} bg-gradient-to-br from-azure-500 to-azure-600 rounded-full flex items-center justify-center flex-shrink-0`}>
          <span className={`${classes.icon} text-white font-bold`}>
            {getInitials(user.name)}
          </span>
        </div>

        {/* User Info */}
        <div className="flex-1 min-w-0">
          <h3 className={`${classes.name} font-semibold text-gray-900 truncate`}>
            {getDisplayName()}
          </h3>
          <div className="flex items-center text-gray-500 mt-1">
            <svg className={`${classes.email} mr-1 flex-shrink-0`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <p className={`${classes.email} truncate`}>{user.email}</p>
          </div>

          {/* Roles */}
          {showRoles && user.roles && user.roles.length > 0 && (
            <div className="flex items-center space-x-2 mt-2">
              <svg className={`${classes.role} text-azure-600 flex-shrink-0`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <div className="flex flex-wrap gap-1">
                {user.roles.map((role, index) => (
                  <span
                    key={index}
                    className={`${classes.role} inline-flex items-center px-2 py-0.5 rounded-full bg-azure-100 text-azure-700 font-medium`}
                  >
                    {formatRole(role)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
