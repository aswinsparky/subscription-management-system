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

  // Customer portal direct access
  if (user?.role === 'CUSTOMER') {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
        <header className="border-b border-slate-800 bg-slate-950/90 backdrop-blur sticky top-0 z-40 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-indigo-600 p-2 rounded-xl text-white">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-base text-white tracking-wide">Brightloop Nexus</h1>
              <p className="text-[11px] text-indigo-400 font-medium">Customer Self-Service Portal</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-xs text-slate-300 font-medium">{user.full_name}</span>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </header>

        <div className="bg-slate-950/80 border-b border-slate-800/80 px-6 py-2 flex items-center space-x-2">
          <button
            onClick={() => setCurrentTab('portal')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold ${currentTab === 'portal' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
          >
            My Subscriptions & Quotes
          </button>
          <button
            onClick={() => setCurrentTab('invoices')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold ${currentTab === 'invoices' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
          >
            My Invoices & Receipts
          </button>
        </div>

        <main className="flex-1 max-w-7xl w-full mx-auto p-6">
          {currentTab === 'portal' && <CustomerPortalPage />}
          {currentTab === 'invoices' && <InvoicesPage />}
        </main>
      </div>
    );
  }

  const navItems = [
    // Financial Intelligence (Member 2)
    { id: 'revenue', label: 'Revenue Hub', icon: LayoutDashboard },
    { id: 'invoices', label: 'Invoices & PDF', icon: FileText },
    { id: 'payments', label: 'Payments', icon: CreditCard },
    { id: 'reconciliation', label: 'Reconciliation', icon: Scale },
    { id: 'guardian', label: 'Revenue Guardian', icon: ShieldAlert },
    { id: 'simulator', label: 'Revenue Simulator', icon: Sparkles },
    { id: 'ai', label: 'Ask Brightloop', icon: Bot },
    { id: 'taxes', label: 'Taxes & Discounts', icon: Percent },
    { id: 'recovery', label: 'Self-Healing', icon: HeartHandshake },

    // Core Subscriptions (Member 1)
    { id: 'customers', label: 'Customers', icon: Users },
    { id: 'products', label: 'Products & Pricing', icon: Package },
    { id: 'plans', label: 'Plans', icon: Calendar },
    { id: 'quotations', label: 'Quotations', icon: FileCheck2 },
    { id: 'subscriptions', label: 'Subscriptions', icon: Repeat },
    { id: 'renewals', label: 'Renewals', icon: RefreshCw },
    { id: 'churn', label: 'Churn Radar', icon: Radar },
    { id: 'timemachine', label: 'Time Machine', icon: History },
    { id: 'overview', label: 'Diagnostics', icon: Cpu },
  ];

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Enterprise Top Navigation Header */}
      <header className="border-b border-slate-800 bg-slate-950/90 backdrop-blur sticky top-0 z-40 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-indigo-600 p-2 rounded-xl shadow-lg shadow-indigo-500/30 text-white">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-base text-white tracking-wide">
              Brightloop Nexus
            </h1>
            <p className="text-[11px] text-indigo-400 font-medium">
              Intelligent Subscription & Financial Revenue Engine
            </p>
          </div>
        </div>

        {/* Current User Session & Actions */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl">
            <div className="w-6 h-6 rounded-lg bg-indigo-950 border border-indigo-800 flex items-center justify-center font-bold text-indigo-300 text-xs">
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
              className="hidden lg:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition"
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>+ Staff</span>
            </button>
          )}

          <button
            onClick={logout}
            title="Sign Out"
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Sub-Header Horizontal Module Navigation Strip */}
      <div className="bg-slate-950/80 border-b border-slate-800/80 px-6 py-2 overflow-x-auto">
        <nav className="flex items-center space-x-1 text-xs font-medium min-w-max">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id as TabType)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl transition ${
                  isActive
                    ? 'bg-indigo-600 text-white font-bold shadow-md shadow-indigo-600/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Main Dynamic Viewport Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8">
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
      </main>

      {/* Staff Modal */}
      {isStaffModalOpen && (
        <CreateStaffModal
          isOpen={isStaffModalOpen}
          onClose={() => setIsStaffModalOpen(false)}
          onStaffCreated={() => fetchUsers()}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-500">
        Brightloop Nexus Enterprise Platform — Developed collaboratively across Member 1 & Member 2 modules.
      </footer>
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
