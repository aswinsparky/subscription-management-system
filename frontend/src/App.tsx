import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth, User } from './context/AuthContext';
import { apiClient } from './api/client';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';
import { CustomerListPage } from './pages/customers/CustomerListPage';
import { ProductListPage } from './pages/products/ProductListPage';
import { PlanListPage } from './pages/plans/PlanListPage';
import { QuotationListPage } from './pages/quotations/QuotationListPage';
import { SubscriptionListPage } from './pages/subscriptions/SubscriptionListPage';
import { RenewalManagementPage } from './pages/renewals/RenewalManagementPage';
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
  CheckCircle2,
  LayoutDashboard,
  Package,
  Calendar,
  FileCheck2,
  Repeat
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

function MainLayout() {
  const { user, logout } = useAuth();
  const [currentTab, setCurrentTab] = useState<'overview' | 'customers' | 'products' | 'plans' | 'quotations' | 'subscriptions' | 'renewals'>('overview');
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
        // Silently catch
      }
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchUsers();
  }, [user]);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Enterprise Top Navigation Header */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3">
            <div className="bg-indigo-600 p-2 rounded-lg shadow-lg shadow-indigo-500/30 text-white">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-base text-white tracking-wide">
                Brightloop Nexus
              </h1>
              <p className="text-[11px] text-indigo-400 font-medium">
                Member 1: Subscription & Intelligence Engine
              </p>
            </div>
          </div>

          {/* Navigation Module Tabs */}
          <nav className="hidden md:flex items-center space-x-1 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs font-semibold">
            <button
              onClick={() => setCurrentTab('overview')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition ${
                currentTab === 'overview'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              <span>Overview</span>
            </button>

            <button
              onClick={() => setCurrentTab('customers')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition ${
                currentTab === 'customers'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>Customers</span>
            </button>

            <button
              onClick={() => setCurrentTab('products')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition ${
                currentTab === 'products'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Package className="w-3.5 h-3.5" />
              <span>Products & Pricing</span>
            </button>

            <button
              onClick={() => setCurrentTab('plans')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition ${
                currentTab === 'plans'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>Subscription Plans</span>
            </button>

            <button
              onClick={() => setCurrentTab('quotations')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition ${
                currentTab === 'quotations'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileCheck2 className="w-3.5 h-3.5" />
              <span>Quotations</span>
            </button>

            <button
              onClick={() => setCurrentTab('subscriptions')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition ${
                currentTab === 'subscriptions'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Repeat className="w-3.5 h-3.5" />
              <span>Subscriptions</span>
            </button>

            <button
              onClick={() => setCurrentTab('renewals')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition ${
                currentTab === 'renewals'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Renewals</span>
            </button>
          </nav>
        </div>

        {/* Current User Session & Actions */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl">
            <div className="w-7 h-7 rounded-lg bg-indigo-950 border border-indigo-800 flex items-center justify-center font-bold text-indigo-300 text-xs">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-xs font-semibold text-white leading-tight">
                {user?.full_name}
              </div>
              <div className="text-[10px] text-slate-400 font-mono">
                {user?.email}
              </div>
            </div>
            <span
              className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${
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
              className="hidden lg:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition"
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>+ Staff</span>
            </button>
          )}

          <button
            onClick={logout}
            title="Sign Out"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8 space-y-8">
        {currentTab === 'customers' ? (
          <CustomerListPage />
        ) : currentTab === 'products' ? (
          <ProductListPage />
        ) : currentTab === 'plans' ? (
          <PlanListPage />
        ) : currentTab === 'quotations' ? (
          <QuotationListPage />
        ) : currentTab === 'subscriptions' ? (
          <SubscriptionListPage />
        ) : currentTab === 'renewals' ? (
          <RenewalManagementPage />
        ) : (
          <>
            {/* Overview Banner */}
            <div className="bg-gradient-to-r from-indigo-950/70 via-slate-900 to-slate-900 p-8 rounded-2xl border border-indigo-900/40 shadow-2xl">
              <div className="max-w-3xl space-y-3">
                <div className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-emerald-400 bg-emerald-950/80 px-3 py-1 rounded-md border border-emerald-800/60">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Phase 1, 2, 3 & 4 Active — Pricing & Multi-Variant Catalog Live</span>
                </div>
                <h2 className="text-3xl font-extrabold text-white tracking-tight">
                  Enterprise Subscription & Revenue Engine
                </h2>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Module 3 (Product & Variant Management) is active with multi-tier price calculations (Base + Variant = Line Total), safe archive guards, and customer management. Click on <strong>Products & Pricing</strong> or <strong>Customers</strong> in the navigation header above.
                </p>
              </div>
            </div>

            {/* Live Diagnostics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
                    <span className="text-xs px-2 py-0.5 rounded bg-emerald-900/60 text-emerald-300 font-mono">15 Tables</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Database: <span className="font-mono text-slate-200">{health?.database.current_database || 'brightloop_nexus'}</span>
                  </p>
                </div>
                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Storage Engine:</span>
                  <span className="text-amber-400 font-mono">InnoDB • DECIMAL(12,2)</span>
                </div>
              </div>

              <div className="bg-slate-950/60 p-6 rounded-xl border border-slate-800 space-y-4 hover:border-slate-700 transition">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Security & RBAC</span>
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
                  <span className="text-slate-500">Tenant Protection:</span>
                  <span className="text-emerald-400 font-medium">Backend Ownership Checks</span>
                </div>
              </div>

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
                    Endpoints: <span className="font-mono text-slate-200">/api/v1/customers/*, /auth/*</span>
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

            {/* RBAC Capabilities Matrix */}
            <div className="bg-slate-950/80 rounded-xl border border-slate-800 p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Shield className="w-5 h-5 text-indigo-400" />
                  <h3 className="font-bold text-sm text-slate-200">
                    Role-Based Access Control Matrix
                  </h3>
                </div>
                <span className="text-xs text-slate-500 font-mono">
                  Current Session: {user?.role}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className={`p-4 rounded-xl border ${user?.role === 'ADMIN' ? 'bg-indigo-950/40 border-indigo-700' : 'bg-slate-900/40 border-slate-800 opacity-60'}`}>
                  <span className="font-bold text-rose-400 uppercase tracking-wider block mb-1">ADMIN Role</span>
                  <ul className="space-y-1 text-slate-300">
                    <li>✓ Create & manage Staff accounts</li>
                    <li>✓ Create, edit & view all Customers</li>
                    <li>✓ Manage products, variants & plans</li>
                    <li>✓ View Churn Radar & Time Machine</li>
                  </ul>
                </div>

                <div className={`p-4 rounded-xl border ${user?.role === 'STAFF' ? 'bg-indigo-950/40 border-indigo-700' : 'bg-slate-900/40 border-slate-800 opacity-60'}`}>
                  <span className="font-bold text-amber-400 uppercase tracking-wider block mb-1">STAFF Role</span>
                  <ul className="space-y-1 text-slate-300">
                    <li>✓ Create & manage Customer profiles</li>
                    <li>✓ Create & send Quotations</li>
                    <li>✓ Manage permitted Subscriptions</li>
                    <li>✗ Cannot create staff accounts</li>
                  </ul>
                </div>

                <div className={`p-4 rounded-xl border ${user?.role === 'CUSTOMER' ? 'bg-indigo-950/40 border-indigo-700' : 'bg-slate-900/40 border-slate-800 opacity-60'}`}>
                  <span className="font-bold text-emerald-400 uppercase tracking-wider block mb-1">CUSTOMER Role</span>
                  <ul className="space-y-1 text-slate-300">
                    <li>✓ View and edit own Customer Profile</li>
                    <li>✓ View personal Quotations & Subscriptions</li>
                    <li>✓ Request pause, resume or renewal</li>
                    <li>✗ Blocked from other customers' data</li>
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
                      System Users & Roles ({userList.length})
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
                  5 of 12 Phases Completed
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { num: '01', title: 'Project Setup & MySQL', status: 'COMPLETED', desc: 'FastAPI, MySQL 8.0, PyMySQL, Vite, React TS' },
                  { num: '02', title: 'Auth & RBAC Schema', status: 'COMPLETED', desc: 'Admin, Staff, Customer JWT, bcrypt, Alembic' },
                  { num: '03', title: 'Customer Management', status: 'COMPLETED', desc: 'CRUD, search, filter, pagination, user linking' },
                  { num: '04', title: 'Product & Variants', status: 'COMPLETED', desc: 'Multi-variant pricing calculation engine' },
                  { num: '05', title: 'Subscription Plans', status: 'COMPLETED', desc: 'Billing intervals, rules, auto-close configs' },
                  { num: '06', title: 'Quotation Management', status: 'NEXT', desc: 'Templates, pricing lines, conversion guard' },
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
          </>
        )}
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
                <MainLayout />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
