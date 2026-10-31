import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, RefreshCw } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: Array<'ADMIN' | 'STAFF' | 'CUSTOMER'>;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        <div className="flex items-center space-x-2 text-sm font-mono">
          <RefreshCw className="w-5 h-5 animate-spin text-indigo-500" />
          <span>Verifying security session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="min-h-screen bg-slate-950 p-8 flex items-center justify-center text-slate-100">
        <div className="max-w-md w-full bg-slate-900 border border-rose-900/50 p-6 rounded-2xl text-center space-y-4 shadow-2xl">
          <div className="inline-flex p-3 rounded-full bg-rose-950 text-rose-400 border border-rose-800">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-white">403 — Access Denied</h2>
          <p className="text-sm text-slate-400">
            Your current account role is <span className="font-mono text-indigo-400 font-semibold">{user.role}</span>. This view requires one of the following permissions: {allowedRoles.join(', ')}.
          </p>
          <a
            href="/"
            className="inline-block px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition"
          >
            Return to Dashboard
          </a>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
