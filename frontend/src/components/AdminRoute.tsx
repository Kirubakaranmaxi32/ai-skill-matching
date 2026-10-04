import React, { useEffect, useState } from 'react';
import { Navigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { checkAdminStatus } from '../services/admin';
import { Loader2, ShieldAlert, ArrowLeft } from 'lucide-react';

interface AdminRouteProps {
  children: React.ReactNode;
}

export const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
  const { user, loading: authLoading } = useAuth();
  const location = useLocation();
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);
  const [checkingAdmin, setCheckingAdmin] = useState<boolean>(true);

  useEffect(() => {
    if (authLoading) return;

    if (!user) {
      setCheckingAdmin(false);
      setIsAdmin(false);
      return;
    }

    // Check fast client-side claim if present
    if (user.app_metadata && (user.app_metadata.role === 'admin' || user.app_metadata.role === 'super_admin')) {
      setIsAdmin(true);
      setCheckingAdmin(false);
      return;
    }

    // Verify against backend server /admin/status
    checkAdminStatus()
      .then((data) => {
        setIsAdmin(Boolean(data.is_admin));
      })
      .catch(() => {
        setIsAdmin(false);
      })
      .finally(() => {
        setCheckingAdmin(false);
      });
  }, [user, authLoading]);

  if (authLoading || checkingAdmin) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-3">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
        <p className="text-sm text-slate-500 font-medium">Verifying administrator authorization...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!isAdmin) {
    return (
      <div className="max-w-2xl mx-auto py-16 px-4 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 text-red-600 mb-6">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Access Denied</h1>
        <p className="text-slate-600 mb-6">
          Administrative privileges are required to view the Admin Dashboard. Your account does not have authorization.
        </p>
        <Link
          to="/dashboard"
          className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium text-sm transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Student Dashboard</span>
        </Link>
      </div>
    );
  }

  return <>{children}</>;
};
