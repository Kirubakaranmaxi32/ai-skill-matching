import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-3">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
        <p className="text-sm text-slate-500 font-medium">Checking authentication status...</p>
      </div>
    );
  }

  if (!user) {
    // If an auth token is in localStorage, session state is settling
    const hasLocalToken = Object.keys(localStorage).some(
      (key) => (key.startsWith('sb-') && key.endsWith('-auth-token')) || key.includes('auth-token')
    );
    if (hasLocalToken) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-3">
          <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
          <p className="text-sm text-slate-500 font-medium">Establishing authenticated session...</p>
        </div>
      );
    }

    // Redirect to login preserving intended target path
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};
