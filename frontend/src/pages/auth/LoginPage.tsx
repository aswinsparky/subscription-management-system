import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth, User } from '../../context/AuthContext';
import { apiClient } from '../../api/client';
import { Lock, Mail, AlertCircle, ArrowRight, ShieldCheck } from 'lucide-react';

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await apiClient.post<LoginResponse>('/auth/login', {
        email: email.trim(),
        password,
      });
      login(res.data.access_token, res.data.user);
      navigate('/');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Invalid email or password credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillQuickLogin = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-2">
        <div className="inline-flex p-3 rounded-2xl bg-indigo-600 shadow-xl shadow-indigo-500/20 text-white mb-2">
          <ShieldCheck className="w-8 h-8" />
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight text-white">
          Sign In to Brightloop Nexus
        </h2>
        <p className="text-sm text-slate-400">
          Intelligent Subscription & Revenue Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-900 py-8 px-6 shadow-2xl rounded-2xl border border-slate-800 sm:px-10 space-y-6">
          {error && (
            <div className="p-3.5 rounded-lg bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@brightloop.io"
                  className="w-full pl-10 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-sm focus:outline-none focus:border-indigo-500 transition"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Password
                </label>
                <Link
                  to="/reset-password"
                  className="text-xs text-indigo-400 hover:text-indigo-300 transition"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-sm focus:outline-none focus:border-indigo-500 transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/30 flex items-center justify-center space-x-2 transition disabled:opacity-50"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Pre-fill shortcuts */}
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <p className="text-xs font-semibold uppercase text-slate-500 tracking-wider">
              Quick Demo Roles:
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => fillQuickLogin('admin@brightloop.io', 'Admin@123456!')}
                className="px-2.5 py-1.5 text-xs font-mono bg-slate-950 hover:bg-slate-800 text-indigo-400 border border-slate-800 rounded-md text-left transition"
              >
                ⚡ ADMIN
              </button>
              <button
                type="button"
                onClick={() => fillQuickLogin('staff@brightloop.io', 'StaffPassword123!')}
                className="px-2.5 py-1.5 text-xs font-mono bg-slate-950 hover:bg-slate-800 text-amber-400 border border-slate-800 rounded-md text-left transition"
              >
                ⚡ STAFF
              </button>
            </div>
          </div>

          <div className="text-center pt-2">
            <span className="text-xs text-slate-400">Don't have an account? </span>
            <Link
              to="/register"
              className="text-xs text-indigo-400 font-semibold hover:text-indigo-300 transition"
            >
              Register Customer Profile
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
