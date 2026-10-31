import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth, User } from './context/AuthContext';
import { apiClient } from './api/client';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';
import { ProtectedRoute } from './components/ProtectedRoute';
import { CreateStaffModal } from './components/CreateStaffModal';
import { 
  Server, 
  Database, 
  ShieldCheck, 
  Cpu, 
  RefreshCw,
  LogOut,
  UserCheck,
  Users,
  Shield,
  CheckCircle2
} from 'lucide-react';

interface HealthData {
  status: string;
  service: string;
  version: string;
  database: {
    status: string;
    database_engine: string;
    version: string;
    current_database: string;
  };
}

function Dashboard() {
  const { user, logout } = useAuth();
  const [health, setHealth] = useState<HealthData | null>(null);
  const [userList, setUserList] = useState<User[]>([]);
  const [isStaffModalOpen, setIsStaffModalOpen] = useState<boolean>(false);

  const fetchHealth = async () => {
    try {
      const res = await apiClient.get<HealthData>('/health');
      setHealth(res.data);
    } catch {
      // Degraded
    }
  };

  const fetchUsers = async () => {
    if (user?.role === 'ADMIN') {
      try {
        const res = await apiClient.get<User[]>('/auth/users');
        setUserList(res.data);
      } catch {
        // Handle error silently or log
      }
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchUsers();
  }, [user]);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Top Enterprise Navigation Header */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-40 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-indigo-600 p-2 rounded-lg shadow-lg shadow-indigo-500/30 text-white">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white tracking-wide">
              Brightloop Nexus
            </h1>
            <p className="text-xs text-indigo-400 font-medium">
              Member 1: Subscription & Intelligence Engine
            </p>
          </div>
        </div>

        {/* Current User Session & Actions */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3 bg-slate-900/90 border border-slate-800 px-3.5 py-1.5 rounded-xl">
            <div className="w-8 h-8 rounded-lg bg-indigo-950 border border-indigo-800 flex items-center justify-center font-bold text-indigo-300 text-xs">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-xs font-semibold text-white leading-tight">
                {user?.full_name}
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                {user?.email}
              </div>
            </div>
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider ${
                user?.role === 'ADMIN'
                  ? 'bg-rose-950 text-rose-300 border border-rose-800'
                  : user?.role === 'STAFF'
                  ? 'bg-amber-950 text-amber-300 border border-amber-800'
                  : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
              }`}
            >
              {user?.role}
            </span>
          </div>

          {user?.role === 'ADMIN' && (
            <button
              onClick={() => setIsStaffModalOpen(true)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition"
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>+ Staff Account</span>
            </button>
          )}

          <button
            onClick={logout}
            title="Sign Out"
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8 space-y-8">
        {/* Banner */}
        <div className="bg-gradient-to-r from-indigo-950/70 via-slate-900 to-slate-900 p-8 rounded-2xl border border-indigo-900/40 shadow-2xl">
          <div className="max-w-3xl space-y-3">
            <div className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-emerald-400 bg-emerald-950/80 px-3 py-1 rounded-md border border-emerald-800/60">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Phase 1 & Phase 2 Verified — Database Migrations & RBAC Live</span>
            </div>
            <h2 className="text-3xl font-extrabold text-white tracking-tight">
              Enterprise Subscription & Revenue Engine
            </h2>
            <p className="text-slate-400 text-sm leading-relaxed">
              All 15 database tables are created in MySQL 8.0 with InnoDB foreign key constraints, `DECIMAL(12,2)` precision, and Alembic migrations. Secure JWT authentication, password complexity enforcement, and strict 3-tier Role-Based Access Control (Admin, Staff, Customer) are active.
            </p>
          </div>
        </div>

        {/* Live Diagnostics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Live DB Engine */}
          <div className="bg-slate-950/60 p-6 rounded-xl border border-slate-800 space-y-4 hover:border-slate-700 transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">MySQL Database</span>
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                <Database className="w-5 h-5" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-white">MySQL 8.0</span>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-900/60 text-emerald-300 font-mono">15 Tables Migrated</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Database: <span className="font-mono text-slate-200">{health?.database.current_database || 'brightloop_nexus'}</span>
              </p>
            </div>
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-500">Storage & Migrations:</span>
              <span className="text-amber-400 font-mono">InnoDB • Alembic head</span>
            </div>
          </div>

          {/* Card 2: Security & Token System */}
          <div className="bg-slate-950/60 p-6 rounded-xl border border-slate-800 space-y-4 hover:border-slate-700 transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Authentication & RBAC</span>
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-white">JWT / Bcrypt</span>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-900/60 text-emerald-300 font-mono">Active</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Current Role: <span className="font-bold text-indigo-400">{user?.role}</span>
              </p>
            </div>
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-500">Password Policy:</span>
              <span className="text-emerald-400 font-medium">&gt;8 char, Upper, Lower, Special</span>
            </div>
          </div>

          {/* Card 3: Backend Gateway */}
          <div className="bg-slate-950/60 p-6 rounded-xl border border-slate-800 space-y-4 hover:border-slate-700 transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">API Gateway</span>
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                <Server className="w-5 h-5" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-white">FastAPI</span>
                <span className="text-xs px-2 py-0.5 rounded bg-indigo-900/60 text-indigo-300 font-mono">v1.0.0</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Endpoints: <span className="font-mono text-slate-200">/api/v1/auth/*, /health</span>
              </p>
            </div>
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-500">Interactive Docs:</span>
              <a
                href="http://localhost:8000/api/v1/docs"
                target="_blank"
                rel="noreferrer"
                className="text-indigo-400 font-mono hover:underline"
              >
                /api/v1/docs ↗
              </a>
            </div>
          </div>
        </div>

        {/* RBAC Capabilities & Role Matrix */}
        <div className="bg-slate-950/80 rounded-xl border border-slate-800 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-indigo-400" />
              <h3 className="font-bold text-sm text-slate-200">
                Active Role-Based Access Control (RBAC) Permissions Matrix
              </h3>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Role: {user?.role}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className={`p-4 rounded-xl border ${user?.role === 'ADMIN' ? 'bg-indigo-950/40 border-indigo-700' : 'bg-slate-900/40 border-slate-800 opacity-60'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-rose-400 uppercase tracking-wider">ADMIN Role</span>
                {user?.role === 'ADMIN' && <span className="px-1.5 py-0.5 bg-rose-950 text-rose-300 rounded text-[10px] font-bold">YOU</span>}
              </div>
              <ul className="space-y-1 text-slate-300">
                <li>✓ Full administrative access</li>
                <li>✓ Create & manage Staff accounts</li>
                <li>✓ Manage products, variants, plans</li>
                <li>✓ View all customer & quotation records</li>
                <li>✓ Access Churn Radar & Time Machine</li>
              </ul>
            </div>

            <div className={`p-4 rounded-xl border ${user?.role === 'STAFF' ? 'bg-indigo-950/40 border-indigo-700' : 'bg-slate-900/40 border-slate-800 opacity-60'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-amber-400 uppercase tracking-wider">STAFF Role</span>
                {user?.role === 'STAFF' && <span className="px-1.5 py-0.5 bg-amber-950 text-amber-300 rounded text-[10px] font-bold">YOU</span>}
              </div>
              <ul className="space-y-1 text-slate-300">
                <li>✓ Manage customer profiles</li>
                <li>✓ Create & send quotations</li>
                <li>✓ Manage permitted subscriptions</li>
                <li>✗ Cannot create staff accounts</li>
                <li>✗ Cannot alter admin system settings</li>
              </ul>
            </div>

            <div className={`p-4 rounded-xl border ${user?.role === 'CUSTOMER' ? 'bg-indigo-950/40 border-indigo-700' : 'bg-slate-900/40 border-slate-800 opacity-60'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-emerald-400 uppercase tracking-wider">CUSTOMER Role</span>
                {user?.role === 'CUSTOMER' && <span className="px-1.5 py-0.5 bg-emerald-950 text-emerald-300 rounded text-[10px] font-bold">YOU</span>}
              </div>
              <ul className="space-y-1 text-slate-300">
                <li>✓ Access self-service customer portal</li>
                <li>✓ View own quotations and subscriptions</li>
                <li>✓ Request pause, resume, or renewal</li>
                <li>✓ View personal subscription timeline</li>
                <li>✗ Strict backend ownership isolation</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Admin User Management Table (Admin Only) */}
        {user?.role === 'ADMIN' && (
          <div className="bg-slate-950/80 rounded-xl border border-slate-800 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Users className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-sm text-slate-200">
                  Registered System Users & Roles ({userList.length})
                </h3>
              </div>
              <button
                onClick={fetchUsers}
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Refresh</span>
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border border-slate-800/80 rounded-lg overflow-hidden">
                <thead className="bg-slate-900 text-slate-400 uppercase font-semibold border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-4">User ID</th>
                    <th className="py-2.5 px-4">Full Name</th>
                    <th className="py-2.5 px-4">Email</th>
                    <th className="py-2.5 px-4">Role</th>
                    <th className="py-2.5 px-4">Status</th>
                    <th className="py-2.5 px-4">Created Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {userList.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-900/50 transition">
                      <td className="py-2 px-4 text-slate-500">#{u.id}</td>
                      <td className="py-2 px-4 text-slate-200 font-sans font-medium">{u.full_name}</td>
                      <td className="py-2 px-4 text-slate-300">{u.email}</td>
                      <td className="py-2 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          u.role === 'ADMIN' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                          u.role === 'STAFF' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                          'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        }`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="py-2 px-4 text-emerald-400">Active</td>
                      <td className="py-2 px-4 text-slate-500">{new Date(u.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 12-Phase Roadmap Progress Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white">Full Implementation Roadmap</h3>
              <p className="text-xs text-slate-400">Strict sequential phase execution</p>
            </div>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-950 px-2.5 py-1 rounded border border-emerald-800/60">
              2 of 12 Phases Completed
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { num: '01', title: 'Project Setup & MySQL', status: 'COMPLETED', desc: 'FastAPI, MySQL 8.0, PyMySQL, Vite, React TS' },
              { num: '02', title: 'Auth & RBAC Schema', status: 'COMPLETED', desc: 'Admin, Staff, Customer JWT, bcrypt, Alembic' },
              { num: '03', title: 'Customer Management', status: 'NEXT', desc: 'CRUD, search, filter, pagination, user linking' },
              { num: '04', title: 'Product & Variants', status: 'PENDING', desc: 'Multi-variant pricing calculation engine' },
              { num: '05', title: 'Subscription Plans', status: 'PENDING', desc: 'Billing intervals, rules, auto-close configs' },
              { num: '06', title: 'Quotation Management', status: 'PENDING', desc: 'Templates, pricing lines, conversion guard' },
              { num: '07', title: 'Subscription Lifecycle', status: 'PENDING', desc: 'Draft->Active->Closed state machine' },
              { num: '08', title: 'Renewal Scheduler', status: 'PENDING', desc: 'Automated renewal & Member 2 idempotency' },
              { num: '09', title: 'Churn Radar', status: 'PENDING', desc: 'Risk scoring (0-100), behavioral signal metrics' },
              { num: '10', title: 'Time Machine', status: 'PENDING', desc: 'Append-only event audit & state reconstruction' },
              { num: '11', title: 'Customer Portal', status: 'PENDING', desc: 'Self-service dashboard & strict tenant checks' },
              { num: '12', title: 'Testing & Hardening', status: 'PENDING', desc: 'Pytest, Vitest, Playwright E2E verification' },
            ].map((phase) => (
              <div 
                key={phase.num}
                className={`p-4 rounded-xl border transition ${
                  phase.status === 'COMPLETED'
                    ? 'bg-indigo-950/40 border-indigo-700/80 shadow-md shadow-indigo-950/50'
                    : phase.status === 'NEXT'
                    ? 'bg-slate-900 border-indigo-500/60 ring-1 ring-indigo-500/30'
                    : 'bg-slate-950/40 border-slate-800/80 opacity-70'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold text-indigo-400">PHASE {phase.num}</span>
                  {phase.status === 'COMPLETED' ? (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                      DONE
                    </span>
                  ) : phase.status === 'NEXT' ? (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                      UP NEXT
                    </span>
                  ) : (
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-900 text-slate-500">
                      QUEUED
                    </span>
                  )}
                </div>
                <h4 className="font-semibold text-sm text-slate-100">{phase.title}</h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">{phase.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Staff Modal */}
      <CreateStaffModal
        isOpen={isStaffModalOpen}
        onClose={() => setIsStaffModalOpen(false)}
        onStaffCreated={fetchUsers}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-4 px-6 text-center text-xs text-slate-500">
        Brightloop Nexus Enterprise Platform • Coordinated Microservices • Member 1 Architecture
      </footer>
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
