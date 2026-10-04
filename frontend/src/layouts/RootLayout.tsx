import React, { useEffect, useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { checkRootHealth } from '../services/api';
import { checkAdminStatus } from '../services/admin';
import { Users, LayoutDashboard, User, FolderKanban, LogIn, UserPlus, LogOut, CheckCircle2, AlertCircle, Sparkles, Mail, Shield } from 'lucide-react';

export const RootLayout: React.FC = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [isAdmin, setIsAdmin] = useState<boolean>(false);

  useEffect(() => {
    checkRootHealth()
      .then((data) => {
        if (data.status === 'healthy') {
          setBackendHealthy(true);
        } else {
          setBackendHealthy(false);
        }
      })
      .catch(() => {
        setBackendHealthy(false);
      });
  }, []);

  useEffect(() => {
    if (!user) {
      setIsAdmin(false);
      return;
    }
    if (user.app_metadata && (user.app_metadata.role === 'admin' || user.app_metadata.role === 'super_admin')) {
      setIsAdmin(true);
      return;
    }
    checkAdminStatus()
      .then((data) => {
        setIsAdmin(Boolean(data.is_admin));
      })
      .catch(() => {
        setIsAdmin(false);
      });
  }, [user]);

  return (
    <div className="flex flex-col min-h-screen">
      {/* Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-200 group-hover:scale-105 transition-transform">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-slate-900 tracking-tight">AI Skill Matching</span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                  DreamMap AI
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium hidden sm:block">Find the right skills. Build the right team.</p>
            </div>
          </Link>

          {/* Navigation Links & System Health */}
          <div className="flex items-center space-x-4 sm:space-x-6">
            <nav className="flex items-center space-x-1 sm:space-x-2">
              <Link
                to="/"
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  location.pathname === '/'
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                Home
              </Link>

              <Link
                to="/dashboard"
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                  location.pathname === '/dashboard'
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>

              {user ? (
                <>
                  <Link
                    to="/profile"
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                      location.pathname === '/profile'
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <User className="w-4 h-4" />
                    <span>Profile</span>
                  </Link>
                  <Link
                    to="/projects"
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                      location.pathname.startsWith('/projects')
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <FolderKanban className="w-4 h-4" />
                    <span>Projects</span>
                  </Link>
                  <Link
                    to="/recommendations"
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                      location.pathname.startsWith('/recommendations')
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <Sparkles className="w-4 h-4 text-indigo-600" />
                    <span>Recommendations</span>
                  </Link>
                  <Link
                    to="/invitations"
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                      location.pathname.startsWith('/invitations')
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <Mail className="w-4 h-4 text-indigo-600" />
                    <span>Invitations</span>
                  </Link>
                  {isAdmin && (
                    <Link
                      to="/admin"
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                        location.pathname.startsWith('/admin')
                          ? 'bg-purple-50 text-purple-700 font-semibold border border-purple-200'
                          : 'text-slate-600 hover:text-purple-700 hover:bg-purple-50'
                      }`}
                    >
                      <Shield className="w-4 h-4 text-purple-600" />
                      <span>Admin</span>
                    </Link>
                  )}
                  <button
                    onClick={() => logout()}
                    className="px-3 py-2 rounded-lg text-sm font-medium text-slate-600 hover:text-rose-600 hover:bg-rose-50 transition-colors flex items-center space-x-1.5"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="hidden sm:inline">Logout</span>
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                      location.pathname === '/login'
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    <LogIn className="w-4 h-4" />
                    <span>Login</span>
                  </Link>

                  <Link
                    to="/register"
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                      location.pathname === '/register'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'
                    }`}
                  >
                    <UserPlus className="w-4 h-4" />
                    <span>Register</span>
                  </Link>
                </>
              )}
            </nav>

            {/* Backend Health Badge */}
            <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-slate-50">
              {backendHealthy === null ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                  <span className="text-slate-500">Checking API...</span>
                </>
              ) : backendHealthy ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  <span className="text-emerald-700">Backend Online</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                  <span className="text-rose-700">Backend Offline</span>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Page Content */}
      <main className="flex-grow">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-sm text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-indigo-500" />
            <span className="font-semibold text-slate-700">AI Skill Matching</span>
            <span>—</span>
            <span>Find the right skills. Build the right team.</span>
          </div>
          <div className="text-xs text-slate-400">
            AI Skill Matching / DreamMap • PyTorch Deep Learning • Supabase PostgreSQL • Protected Sessions
          </div>
        </div>
      </footer>
    </div>
  );
};
