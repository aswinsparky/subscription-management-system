import { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { 
  DollarSign, 
  TrendingUp, 
  Clock, 
  ShieldAlert, 
  RefreshCw,
  Sparkles,
  CreditCard
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';

interface CommandCenterSummary {
  total_revenue: number;
  mrr: number;
  arr: number;
  total_collected: number;
  total_outstanding: number;
  total_overdue: number;
  active_subscriptions: number;
  cancelled_subscriptions: number;
  payment_success_rate: number;
  revenue_leakage_at_risk: number;
}

interface TrendPoint {
  month: string;
  invoiced: number;
  collected: number;
}

interface StatusItem {
  status: string;
  count: number;
  total: number;
}

interface PaymentMethodItem {
  method: string;
  count: number;
  total: number;
}

const COLORS = ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

export function RevenueDashboardPage() {
  const [summary, setSummary] = useState<CommandCenterSummary | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [statusDist, setStatusDist] = useState<StatusItem[]>([]);
  const [methodDist, setMethodDist] = useState<PaymentMethodItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [sumRes, trendRes, statusRes, methodRes] = await Promise.all([
        apiClient.get<CommandCenterSummary>('/analytics/summary'),
        apiClient.get<TrendPoint[]>('/analytics/trends?months=6'),
        apiClient.get<StatusItem[]>('/analytics/status-distribution'),
        apiClient.get<PaymentMethodItem[]>('/analytics/payment-methods'),
      ]);
      setSummary(sumRes.data);
      setTrends(trendRes.data);
      setStatusDist(statusRes.data);
      setMethodDist(methodRes.data);
    } catch (err) {
      console.error('Failed to load revenue dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-950/70 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-1.5 bg-indigo-500/20 text-indigo-400 rounded-lg">
              <Sparkles className="w-4 h-4" />
            </span>
            <span className="text-xs uppercase font-mono tracking-wider text-indigo-400 font-semibold">
              Member 2: Financial Intelligence Engine
            </span>
          </div>
          <h2 className="text-2xl font-extrabold text-white mt-1">Revenue Command Center</h2>
          <p className="text-slate-400 text-xs mt-0.5">
            Real-time financial telemetry, cash collection tracking, and predictive revenue loss prevention.
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Financial Telemetry</span>
        </button>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* MRR */}
        <div className="bg-slate-950/60 p-5 rounded-2xl border border-slate-800/80 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Monthly Recurring Revenue</span>
            <span className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl">
              <TrendingUp className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-black text-white">
              ${summary ? summary.mrr.toLocaleString(undefined, { minimumFractionDigits: 2 }) : '0.00'}
            </span>
            <span className="text-xs text-emerald-400 font-semibold">
              ARR: ${summary ? summary.arr.toLocaleString(undefined, { minimumFractionDigits: 0 }) : '0'}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-400">
            Across <span className="text-indigo-400 font-bold">{summary?.active_subscriptions || 0}</span> active subscriptions
          </div>
        </div>

        {/* Total Invoiced */}
        <div className="bg-slate-950/60 p-5 rounded-2xl border border-slate-800/80 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Invoiced (All-time)</span>
            <span className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl">
              <DollarSign className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2">
            <span className="text-2xl font-black text-white">
              ${summary ? summary.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2 }) : '0.00'}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-400">
            Collected: <span className="text-emerald-400 font-bold">${summary?.total_collected.toLocaleString(undefined, { minimumFractionDigits: 2 }) || '0.00'}</span>
          </div>
        </div>

        {/* Overdue Accounts */}
        <div className="bg-slate-950/60 p-5 rounded-2xl border border-slate-800/80 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Overdue Balances</span>
            <span className="p-2 bg-rose-500/10 text-rose-400 rounded-xl">
              <Clock className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2">
            <span className="text-2xl font-black text-rose-400">
              ${summary ? summary.total_overdue.toLocaleString(undefined, { minimumFractionDigits: 2 }) : '0.00'}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-400">
            Outstanding: ${summary?.total_outstanding.toLocaleString(undefined, { minimumFractionDigits: 2 }) || '0.00'}
          </div>
        </div>

        {/* Revenue Leakage Risk */}
        <div className="bg-slate-950/60 p-5 rounded-2xl border border-slate-800/80 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Revenue Leakage at Risk</span>
            <span className="p-2 bg-amber-500/10 text-amber-400 rounded-xl">
              <ShieldAlert className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2">
            <span className="text-2xl font-black text-amber-400">
              ${summary ? summary.revenue_leakage_at_risk.toLocaleString(undefined, { minimumFractionDigits: 2 }) : '0.00'}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-400">
            Success Rate: <span className="text-emerald-400 font-bold">{summary?.payment_success_rate || 100}%</span>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Invoiced vs Collected Trend (Recharts AreaChart) */}
        <div className="lg:col-span-2 bg-slate-950/60 p-6 rounded-2xl border border-slate-800/80 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-sm text-white">Revenue Invoiced vs. Collected</h3>
              <p className="text-xs text-slate-400">Monthly billing vs. settled cash inflows</p>
            </div>
            <div className="flex items-center space-x-3 text-xs">
              <span className="flex items-center space-x-1 text-indigo-400">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span>
                <span>Invoiced</span>
              </span>
              <span className="flex items-center space-x-1 text-emerald-400">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                <span>Collected</span>
              </span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorInvoiced" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorCollected" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="month" stroke="#64748B" fontSize={11} />
                <YAxis stroke="#64748B" fontSize={11} tickFormatter={(val) => `$${val}`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '12px' }}
                  itemStyle={{ fontSize: '12px' }}
                  formatter={(val: any) => [`$${Number(val).toLocaleString()}`, '']}
                />
                <Area type="monotone" dataKey="invoiced" stroke="#6366F1" fillOpacity={1} fill="url(#colorInvoiced)" strokeWidth={2} />
                <Area type="monotone" dataKey="collected" stroke="#10B981" fillOpacity={1} fill="url(#colorCollected)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Invoice Status Distribution (PieChart) */}
        <div className="bg-slate-950/60 p-6 rounded-2xl border border-slate-800/80 shadow-lg space-y-4 flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-sm text-white">Invoice Portfolio Breakdown</h3>
            <p className="text-xs text-slate-400">Distribution of confirmed, paid & overdue</p>
          </div>

          <div className="h-48 w-full flex items-center justify-center">
            {statusDist.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusDist}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    outerRadius={65}
                    innerRadius={45}
                    paddingAngle={4}
                  >
                    {statusDist.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px' }}
                    itemStyle={{ fontSize: '11px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-slate-500">No invoices generated yet</p>
            )}
          </div>

          <div className="space-y-1.5 border-t border-slate-800/60 pt-3">
            {statusDist.map((item, idx) => (
              <div key={item.status} className="flex items-center justify-between text-xs">
                <span className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }}></span>
                  <span className="text-slate-300 font-medium">{item.status}</span>
                </span>
                <span className="text-slate-400 font-mono font-semibold">${item.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Payment Methods breakdown if available */}
      {methodDist.length > 0 && (
        <div className="bg-slate-950/60 p-6 rounded-2xl border border-slate-800/80 shadow-lg">
          <h3 className="font-bold text-sm text-white flex items-center space-x-2 mb-3">
            <CreditCard className="w-4 h-4 text-indigo-400" />
            <span>Settled Payments by Method</span>
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {methodDist.map((m) => (
              <div key={m.method} className="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
                <div className="text-xs font-semibold text-slate-300">{m.method}</div>
                <div className="text-lg font-black text-emerald-400 font-mono mt-1">
                  ${m.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
                <div className="text-[11px] text-slate-500">{m.count} transaction(s)</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
