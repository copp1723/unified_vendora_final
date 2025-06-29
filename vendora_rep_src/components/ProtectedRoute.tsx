import React from 'react';
import { Redirect } from 'wouter';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
  requireEmailVerified?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requireAdmin = false,
  requireEmailVerified = true 
}) => {
  const { user, userInfo, isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Redirect to="/" />;
  }

  if (requireEmailVerified && !user.emailVerified) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">Email Verification Required</h2>
          <p className="text-gray-600">Please verify your email to access this page.</p>
        </div>
      </div>
    );
  }

  if (requireAdmin && (!userInfo || !userInfo.is_admin)) {
    return <Redirect to="/" />;
  }

  return <>{children}</>;
};
