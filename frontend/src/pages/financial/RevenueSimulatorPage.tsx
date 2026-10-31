import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { 
  Sparkles, 
  Sliders, 
  RefreshCw, 
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
} from 'recharts';

interface MonthlyForecastPoint {
  month_index: number;
  month_label: string;
  baseline_revenue: number;
  projected_revenue: number;
  new_revenue: number;
  churned_revenue: number;
  net_growth: number;
  active_subscriptions: number;
}

interface SimulationResponse {
  scenario_name: string;
  baseline_mrr: number;
  projected_mrr: number;
  net_mrr_impact: number;
  baseline_arr: number;
  projected_arr: number;
  growth_rate_percent: number;
  assumptions_used: any;
  monthly_forecast: MonthlyForecastPoint[];
}

export function RevenueSimulatorPage() {
  const [scenarioName, setScenarioName] = useState('Aggressive Scale Q1');
  const [newCustomers, setNewCustomers] = useState(10);
  const [churnRate, setChurnRate] = useState(2.5);
  const [upgradeRate, setUpgradeRate] = useState(5.0);
  const [priceChange, setPriceChange] = useState(0.0);
  const [discountImpact] = useState(5.0);
  const [months, setMonths] = useState(12);

  const [simulation, setSimulation] = useState<SimulationResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = async () => {
    try {
      setLoading(true);
      const res = await apiClient.post<SimulationResponse>('/revenue-simulator/simulate', {
        scenario_name: scenarioName,
        new_customers_monthly: newCustomers,
        churn_rate_percent: churnRate.toString(),
        plan_upgrade_rate_percent: upgradeRate.toString(),
        price_change_percent: priceChange.toString(),
        discount_campaign_impact_percent: discountImpact.toString(),
        projection_months: months,
      });
      setSimulation(res.data);
    } catch (err) {
      console.error('Failed to run simulation', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950/70 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-1.5 bg-indigo-500/20 text-indigo-400 rounded-lg">
              <Sparkles className="w-4 h-4" />
            </span>
            <span className="text-xs uppercase font-mono tracking-wider text-indigo-400 font-semibold">
              Future Recurring Revenue Engine
            </span>
          </div>
          <h2 className="text-xl font-extrabold text-white mt-1">Future Revenue Simulator</h2>
          <p className="text-slate-400 text-xs mt-0.5">
            Model the financial impact of customer growth, churn shifts, plan upgrades, price changes, and promotions.
          </p>
        </div>

        <button
          onClick={runSimulation}
          disabled={loading}
          className="flex items-center space-x-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Recalculate Projections</span>
        </button>
      </div>

      {/* Main Grid: Parameter Controls on Left, Charts on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls Card */}
        <div className="bg-slate-950/60 p-6 rounded-2xl border border-slate-800/80 shadow-lg space-y-5">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <Sliders className="w-4 h-4 text-indigo-400" />
            <h3 className="font-bold text-sm text-white">Simulation Levers</h3>
          </div>

          <div className="space-y-4 text-xs">
            {/* Scenario Name */}
            <div>
              <label className="block text-slate-400 font-medium mb-1">Scenario Label</label>
              <input
                type="text"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200"
              />
            </div>

            {/* New Customers Monthly */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium mb-1">
                <span>New Customers / Month:</span>
                <span className="text-indigo-400 font-bold font-mono">+{newCustomers}</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={newCustomers}
                onChange={(e) => setNewCustomers(parseInt(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>

            {/* Churn Rate */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium mb-1">
                <span>Monthly Churn Rate:</span>
                <span className="text-rose-400 font-bold font-mono">{churnRate}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="15"
                step="0.5"
                value={churnRate}
                onChange={(e) => setChurnRate(parseFloat(e.target.value))}
                className="w-full accent-rose-500"
              />
            </div>

            {/* Plan Upgrade / Expansion */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium mb-1">
                <span>Plan Upgrade Rate:</span>
                <span className="text-emerald-400 font-bold font-mono">{upgradeRate}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="20"
                step="0.5"
                value={upgradeRate}
                onChange={(e) => setUpgradeRate(parseFloat(e.target.value))}
                className="w-full accent-emerald-500"
              />
            </div>

            {/* Price Change */}
            <div>
              <div className="flex justify-between text-slate-300 font-medium mb-1">
                <span>Price Adjustment:</span>
                <span className="text-amber-400 font-bold font-mono">{priceChange > 0 ? `+${priceChange}%` : `${priceChange}%`}</span>
              </div>
              <input
                type="range"
                min="-20"
                max="50"
                step="5"
                value={priceChange}
                onChange={(e) => setPriceChange(parseFloat(e.target.value))}
                className="w-full accent-amber-500"
              />
            </div>

            {/* Projection Horizon */}
            <div>
              <label className="block text-slate-400 font-medium mb-1">Projection Horizon</label>
              <div className="grid grid-cols-3 gap-2">
                {[6, 12, 24].map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setMonths(m)}
                    className={`py-1.5 rounded-xl font-semibold border text-xs transition ${
                      months === m
                        ? 'bg-indigo-600 border-indigo-500 text-white shadow-md shadow-indigo-600/30'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {m} Mos
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={runSimulation}
              className="w-full mt-2 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl shadow-lg shadow-indigo-600/20 transition"
            >
              Simulate Growth Curve
            </button>
          </div>
        </div>

        {/* Projection Chart & KPI Results on Right */}
        <div className="lg:col-span-2 space-y-6">
          {/* Top Projection KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400">Baseline MRR</div>
              <div className="text-2xl font-black text-white font-mono mt-0.5">
                ${simulation ? Number(simulation.baseline_mrr).toLocaleString(undefined, { minimumFractionDigits: 2 }) : '0.00'}
              </div>
              <div className="text-[11px] text-slate-500 mt-1">Current recurring baseline</div>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400">Projected MRR ({months} Mos)</div>
              <div className="text-2xl font-black text-emerald-400 font-mono mt-0.5">
                ${simulation ? Number(simulation.projected_mrr).toLocaleString(undefined, { minimumFractionDigits: 2 }) : '0.00'}
              </div>
              <div className="text-[11px] text-emerald-400/80 mt-1">
                ARR: ${simulation ? Number(simulation.projected_arr).toLocaleString(undefined, { minimumFractionDigits: 0 }) : '0'}
              </div>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400">Projected Growth</div>
              <div className="text-2xl font-black text-indigo-400 font-mono mt-0.5">
                +{simulation ? Number(simulation.growth_rate_percent).toFixed(1) : 0}%
              </div>
              <div className="text-[11px] text-indigo-400/80 mt-1">
                Net Impact: +${simulation ? Number(simulation.net_mrr_impact).toLocaleString(undefined, { minimumFractionDigits: 0 }) : '0'}
              </div>
            </div>
          </div>

          {/* Forecasting Curve (Recharts LineChart) */}
          <div className="bg-slate-950/60 p-6 rounded-2xl border border-slate-800/80 shadow-lg space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-white">Projected MRR vs. Actual Baseline</h3>
                <p className="text-xs text-slate-400">Continuous forward cohort projection</p>
              </div>
              <div className="flex items-center space-x-3 text-xs">
                <span className="flex items-center space-x-1 text-slate-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
                  <span>Baseline</span>
                </span>
                <span className="flex items-center space-x-1 text-emerald-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                  <span>Projected</span>
                </span>
              </div>
            </div>

            <div className="h-72 w-full">
              {simulation && simulation.monthly_forecast.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={simulation.monthly_forecast} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="month_label" stroke="#64748B" fontSize={11} />
                    <YAxis stroke="#64748B" fontSize={11} tickFormatter={(val) => `$${val}`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '12px' }}
                      formatter={(val: any) => [`$${Number(val).toLocaleString()}`, '']}
                    />
                    <Line type="monotone" dataKey="baseline_revenue" stroke="#64748B" strokeDasharray="5 5" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="projected_revenue" stroke="#10B981" strokeWidth={3} dot={{ fill: '#10B981', r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">
                  Running simulation...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

