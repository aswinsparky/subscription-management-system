import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth, User } from './context/AuthContext';
import { apiClient } from './api/client';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';

// Member 1 Pages
import { CustomerListPage } from './pages/customers/CustomerListPage';
import { ProductListPage } from './pages/products/ProductListPage';
import { PlanListPage } from './pages/plans/PlanListPage';
import { QuotationListPage } from './pages/quotations/QuotationListPage';
import { SubscriptionListPage } from './pages/subscriptions/SubscriptionListPage';
import { RenewalManagementPage } from './pages/renewals/RenewalManagementPage';
import { ChurnRadarPage } from './pages/churn/ChurnRadarPage';
import { TimeMachinePage } from './pages/timemachine/TimeMachinePage';
import { CustomerPortalPage } from './pages/portal/CustomerPortalPage';
import { ProtectedRoute } from './components/ProtectedRoute';
import { CreateStaffModal } from './components/CreateStaffModal';

// Member 2 Financial Intelligence Pages
import { RevenueDashboardPage } from './pages/financial/RevenueDashboardPage';
import { InvoicesPage } from './pages/financial/InvoicesPage';
import { PaymentsPage } from './pages/financial/PaymentsPage';
import { ReconciliationPage } from './pages/financial/ReconciliationPage';
import { RevenueGuardianPage } from './pages/financial/RevenueGuardianPage';
import { RevenueSimulatorPage } from './pages/financial/RevenueSimulatorPage';
import { AskBrightloopAIPage } from './pages/financial/AskBrightloopAIPage';
import { TaxesDiscountsPage } from './pages/financial/TaxesDiscountsPage';
import { BillingRecoveryPage } from './pages/financial/BillingRecoveryPage';

import { 
  Cpu, 
  LogOut, 
  UserCheck, 
  Users, 
  LayoutDashboard,
  Package,
  Calendar,
  FileCheck2,
  Repeat,
  RefreshCw,
  Radar,
  History,
  FileText,
  CreditCard,
  Scale,
  ShieldAlert,
  Sparkles,
  Bot,
  Percent,
  HeartHandshake
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

type TabType = 
  | 'revenue'
  | 'invoices' 
  | 'payments' 
  | 'reconciliation' 
  | 'guardian' 
  | 'simulator' 
  | 'ai' 
  | 'taxes' 
  | 'recovery' 
  | 'customers' 
  | 'products'
  | 'plans'
  | 'quotations'
  | 'subscriptions'
  | 'renewals'
  | 'churn'
  | 'timemachine'
  | 'portal'
  | 'overview';

function MainLayout() {
  const { user, logout } = useAuth();
  const [currentTab, setCurrentTab] = useState<TabType>(
    user?.role === 'CUSTOMER' ? 'portal' : 'revenue'
  );
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

  // Customer Portal direct access with Left Sidebar Layout
  if (user?.role === 'CUSTOMER') {
    return (
      <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
        {/* Customer Left Sidebar */}
        <aside className="w-64 flex-shrink-0 bg-slate-950 border-r border-slate-800 flex flex-col h-full z-30 select-none">
          {/* Brand Header */}
          <div className="p-4 border-b border-slate-800/80 flex items-center space-x-3 flex-shrink-0">
            <div className="bg-indigo-600 p-2 rounded-xl shadow-lg shadow-indigo-600/30 text-white flex-shrink-0">
              <Cpu className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h1 className="font-extrabold text-sm text-white tracking-wide truncate">Brightloop Nexus</h1>
              <p className="text-[10px] text-indigo-400 font-medium truncate">Customer Portal</p>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
            <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 px-3 py-1">
              Self-Service Menu
            </div>
            <button
              onClick={() => setCurrentTab('portal')}
              className={`w-full flex items-center space-x-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold transition ${
                currentTab === 'portal'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/25'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80'
              }`}
            >
              <Repeat className="w-4 h-4" />
              <span>Subscriptions & Quotes</span>
            </button>
            <button
              onClick={() => setCurrentTab('invoices')}
              className={`w-full flex items-center space-x-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold transition ${
                currentTab === 'invoices'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/25'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>Invoices & Receipts</span>
            </button>
          </div>

          {/* Customer User Footer */}
          <div className="p-3 border-t border-slate-800/80 bg-slate-950 space-y-2 flex-shrink-0">
            <div className="flex items-center justify-between p-2 rounded-xl bg-slate-900/80 border border-slate-800/60">
              <div className="flex items-center space-x-2 min-w-0">
                <div className="w-7 h-7 rounded-lg bg-emerald-950 border border-emerald-800 flex items-center justify-center font-bold text-emerald-300 text-xs flex-shrink-0">
                  {user?.full_name?.charAt(0) || 'C'}
                </div>
                <div className="min-w-0 text-left">
                  <div className="text-xs font-semibold text-white truncate leading-tight">
                    {user?.full_name}
                  </div>
                  <div className="text-[10px] text-slate-400 truncate font-mono">
                    {user?.email}
                  </div>
                </div>
              </div>
              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider bg-emerald-950 text-emerald-300 border border-emerald-800 flex-shrink-0">
                CUSTOMER
              </span>
            </div>

            <button
              onClick={logout}
              title="Sign Out"
              className="w-full flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 text-xs font-medium transition"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </aside>

        {/* Customer Content Viewport */}
        <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden bg-slate-900">
          <header className="h-14 border-b border-slate-800 bg-slate-950/70 backdrop-blur px-6 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500 font-medium">Portal /</span>
              <h2 className="text-sm font-bold text-white">
                {currentTab === 'portal' ? 'My Subscriptions & Quotations' : 'My Invoices & Payment History'}
              </h2>
            </div>
            <div className="text-xs text-slate-400 font-mono">
              Secure Tenant Access
            </div>
          </header>

          <main className="flex-1 overflow-y-auto p-6 md:p-8">
            <div className="max-w-7xl mx-auto">
              {currentTab === 'portal' && <CustomerPortalPage />}
              {currentTab === 'invoices' && <InvoicesPage />}
            </div>
          </main>
        </div>
      </div>
    );
  }

  // Admin & Staff Navigation Groups
  const navSections = [
    {
      title: 'Financial Intelligence',
      items: [
        { id: 'revenue', label: 'Revenue Hub', icon: LayoutDashboard },
        { id: 'invoices', label: 'Invoices & PDF', icon: FileText },
        { id: 'payments', label: 'Payments', icon: CreditCard },
        { id: 'reconciliation', label: 'Reconciliation', icon: Scale },
        { id: 'guardian', label: 'Revenue Guardian', icon: ShieldAlert },
        { id: 'simulator', label: 'Revenue Simulator', icon: Sparkles },
        { id: 'ai', label: 'Ask Brightloop', icon: Bot },
        { id: 'taxes', label: 'Taxes & Discounts', icon: Percent },
        { id: 'recovery', label: 'Self-Healing', icon: HeartHandshake },
      ],
    },
    {
      title: 'Subscription Engine',
      items: [
        { id: 'customers', label: 'Customers', icon: Users },
        { id: 'products', label: 'Products & Pricing', icon: Package },
        { id: 'plans', label: 'Plans', icon: Calendar },
        { id: 'quotations', label: 'Quotations', icon: FileCheck2 },
        { id: 'subscriptions', label: 'Subscriptions', icon: Repeat },
        { id: 'renewals', label: 'Renewals', icon: RefreshCw },
        { id: 'churn', label: 'Churn Radar', icon: Radar },
        { id: 'timemachine', label: 'Time Machine', icon: History },
      ],
    },
    {
      title: 'Platform System',
      items: [
        { id: 'overview', label: 'Diagnostics & Health', icon: Cpu },
      ],
    },
  ];

  const allNavItems = navSections.flatMap((s) => s.items);
  const activeNavItem = allNavItems.find((n) => n.id === currentTab);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Left Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-slate-950 border-r border-slate-800 flex flex-col h-full z-30 select-none">
        {/* Brand Header */}
        <div className="p-4 border-b border-slate-800/80 flex items-center space-x-3 flex-shrink-0">
          <div className="bg-indigo-600 p-2 rounded-xl shadow-lg shadow-indigo-600/30 text-white flex-shrink-0">
            <Cpu className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <h1 className="font-extrabold text-sm text-white tracking-wide truncate">Brightloop Nexus</h1>
            <p className="text-[10px] text-indigo-400 font-medium truncate">Revenue & Subscription OS</p>
          </div>
        </div>

        {/* Scrollable Navigation Sections */}
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
          {navSections.map((section) => (
            <div key={section.title} className="space-y-1">
              <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 px-3 py-1">
                {section.title}
              </div>
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = currentTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setCurrentTab(item.id as TabType)}
                      className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-indigo-600 text-white font-bold shadow-md shadow-indigo-600/25'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/90'
                      }`}
                    >
                      <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                      <span className="truncate">{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Sidebar User Footer */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-950 space-y-2 flex-shrink-0">
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-900/80 border border-slate-800/60">
            <div className="flex items-center space-x-2 min-w-0">
              <div className="w-7 h-7 rounded-lg bg-indigo-950 border border-indigo-800 flex items-center justify-center font-bold text-indigo-300 text-xs flex-shrink-0">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <div className="min-w-0 text-left">
                <div className="text-xs font-semibold text-white truncate leading-tight">
                  {user?.full_name}
                </div>
                <div className="text-[10px] text-slate-400 truncate font-mono">
                  {user?.email}
                </div>
              </div>
            </div>
            <span
              className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider flex-shrink-0 ${
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

          <div className="flex items-center space-x-2">
            {user?.role === 'ADMIN' && (
              <button
                onClick={() => setIsStaffModalOpen(true)}
                className="flex-1 flex items-center justify-center space-x-1 py-1.5 px-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition"
              >
                <UserCheck className="w-3.5 h-3.5" />
                <span>+ Staff</span>
              </button>
            )}
            <button
              onClick={logout}
              title="Sign Out"
              className="flex items-center justify-center space-x-1 py-1.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-medium transition flex-shrink-0"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Right Viewport Area */}
      <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden bg-slate-900">
        {/* Right Top Header */}
        <header className="h-14 border-b border-slate-800 bg-slate-950/70 backdrop-blur px-6 flex items-center justify-between flex-shrink-0 z-20">
          <div className="flex items-center space-x-2.5">
            {activeNavItem && (
              <div className="p-1.5 rounded-lg bg-indigo-600/20 text-indigo-400">
                <activeNavItem.icon className="w-4 h-4" />
              </div>
            )}
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500 font-medium">Dashboard /</span>
              <h2 className="text-sm font-bold text-white capitalize">
                {activeNavItem?.label || currentTab}
              </h2>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>{health?.database.database_engine || 'MySQL 8.0'}</span>
            </div>

            {user?.role === 'ADMIN' && (
              <button
                onClick={() => setIsStaffModalOpen(true)}
                className="hidden sm:flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition"
              >
                <UserCheck className="w-3.5 h-3.5" />
                <span>+ Staff</span>
              </button>
            )}

            <button
              onClick={fetchHealth}
              title="Refresh Health"
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </header>

        {/* Scrollable Main Dynamic Viewport */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Member 2 Financial Modules */}
            {currentTab === 'revenue' && <RevenueDashboardPage />}
            {currentTab === 'invoices' && <InvoicesPage />}
            {currentTab === 'payments' && <PaymentsPage />}
            {currentTab === 'reconciliation' && <ReconciliationPage />}
            {currentTab === 'guardian' && <RevenueGuardianPage />}
            {currentTab === 'simulator' && <RevenueSimulatorPage />}
            {currentTab === 'ai' && <AskBrightloopAIPage />}
            {currentTab === 'taxes' && <TaxesDiscountsPage />}
            {currentTab === 'recovery' && <BillingRecoveryPage />}

            {/* Member 1 Modules */}
            {currentTab === 'customers' && <CustomerListPage />}
            {currentTab === 'products' && <ProductListPage />}
            {currentTab === 'plans' && <PlanListPage />}
            {currentTab === 'quotations' && <QuotationListPage />}
            {currentTab === 'subscriptions' && <SubscriptionListPage />}
            {currentTab === 'renewals' && <RenewalManagementPage />}
            {currentTab === 'churn' && <ChurnRadarPage />}
            {currentTab === 'timemachine' && <TimeMachinePage />}

            {/* Overview / Diagnostics */}
            {currentTab === 'overview' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-slate-950/60 p-6 rounded-2xl border border-slate-800 space-y-3">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Database Engine</span>
                    <div className="text-2xl font-black text-white">{health?.database.database_engine || 'MySQL 8.0+'}</div>
                    <p className="text-xs text-slate-400">
                      Version: <span className="font-mono text-slate-200">{health?.database.version || 'Connected'}</span>
                    </p>
                    <div className="pt-2 border-t border-slate-800 text-xs text-amber-400 font-mono">
                      InnoDB • DECIMAL(12, 2)
                    </div>
                  </div>

                  <div className="bg-slate-950/60 p-6 rounded-2xl border border-slate-800 space-y-3">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Security Architecture</span>
                    <div className="text-2xl font-black text-white">JWT • Argon2/Bcrypt</div>
                    <p className="text-xs text-slate-400">
                      Active User Role: <span className="font-bold text-indigo-400">{user?.role}</span>
                    </p>
                    <div className="pt-2 border-t border-slate-800 text-xs text-emerald-400 font-medium">
                      Strict Role-Based Access Control
                    </div>
                  </div>

                  <div className="bg-slate-950/60 p-6 rounded-2xl border border-slate-800 space-y-3">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">API Documentation</span>
                    <div className="text-2xl font-black text-white">FastAPI v1.0.0</div>
                    <p className="text-xs text-slate-400">
                      Swagger UI Interactive Explorer
                    </p>
                    <div className="pt-2 border-t border-slate-800 text-xs">
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

                {/* User List for Admin */}
                {user?.role === 'ADMIN' && userList.length > 0 && (
                  <div className="bg-slate-950/80 rounded-2xl border border-slate-800 p-6 space-y-3">
                    <h3 className="font-bold text-sm text-slate-200">Registered Platform Users</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
                          <tr>
                            <th className="px-4 py-2">ID</th>
                            <th className="px-4 py-2">Full Name</th>
                            <th className="px-4 py-2">Email</th>
                            <th className="px-4 py-2">Role</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 text-slate-300">
                          {userList.map((u) => (
                            <tr key={u.id}>
                              <td className="px-4 py-2 font-mono">{u.id}</td>
                              <td className="px-4 py-2 font-medium text-white">{u.full_name}</td>
                              <td className="px-4 py-2 font-mono text-slate-400">{u.email}</td>
                              <td className="px-4 py-2">
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300">
                                  {u.role}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800/80 py-3 px-6 text-center text-xs text-slate-500 flex-shrink-0 bg-slate-950/40">
          Brightloop Nexus Enterprise Platform — Developed collaboratively across Member 1 & Member 2 modules.
        </footer>
      </div>

      {/* Staff Modal */}
      {isStaffModalOpen && (
        <CreateStaffModal
          isOpen={isStaffModalOpen}
          onClose={() => setIsStaffModalOpen(false)}
          onStaffCreated={() => fetchUsers()}
        />
      )}
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
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
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
