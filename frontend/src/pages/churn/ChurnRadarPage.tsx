import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { ChurnDashboardMetrics, CustomerRiskProfile } from '../../types/churn';
import { 
  Radar, 
  AlertTriangle, 
  ShieldAlert, 
  DollarSign, 
  TrendingDown, 
  Eye, 
  Zap, 
  Activity,
  Send
} from 'lucide-react';

export const ChurnRadarPage: React.FC = () => {
  const [metrics, setMetrics] = useState<ChurnDashboardMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [tierFilter, setTierFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');

  // Inspection & Retention Action Modal
  const [selectedProfile, setSelectedProfile] = useState<CustomerRiskProfile | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [actionType, setActionType] = useState<string>('DISCOUNT_OFFER');
  const [discountPercent, setDiscountPercent] = useState<number>(20);
  const [notes, setNotes] = useState<string>('');
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<ChurnDashboardMetrics>('/churn/dashboard');
      setMetrics(res.data);
    } catch (err) {
      console.error('Failed to load churn metrics', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const handleOpenProfile = async (customer_id: number) => {
    try {
      const res = await apiClient.get<CustomerRiskProfile>(`/churn/customer/${customer_id}`);
      setSelectedProfile(res.data);
      setIsModalOpen(true);
    } catch (err) {
      console.error('Failed to load risk profile', err);
    }
  };

  const handleRetentionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProfile) return;
    try {
      setActionLoading(true);
      await apiClient.post(`/churn/customer/${selectedProfile.customer_id}/retention-action`, {
        action_type: actionType,
        notes: notes || 'Retention intervention logged via Churn Radar HUD.',
        discount_percent_offered: discountPercent,
      });
      alert('Retention action recorded successfully and logged in customer subscription ledger.');
      setIsModalOpen(false);
      setNotes('');
      await fetchMetrics();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to record retention action.');
    } finally {
      setActionLoading(false);
    }
  };

  const filteredCustomers = (metrics?.top_at_risk_customers || []).filter((c) => {
    if (tierFilter === 'ALL') return true;
    return c.risk_tier === tierFilter;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-950/60 p-6 rounded-2xl border border-slate-800">
        <div>
          <div className="flex items-center space-x-2.5 text-rose-400 mb-1">
            <Radar className="w-5 h-5" />
            <h2 className="text-xl font-bold text-white tracking-wide">
              Churn Radar & Behavioral Risk Analytics
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            Algorithmic real-time churn prediction engine analyzing pauses, auto-renewal toggles, and contract signals.
          </p>
        </div>

        <button
          onClick={fetchMetrics}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition self-start md:self-auto"
        >
          <Activity className="w-4 h-4 text-indigo-400" />
          <span>Refresh Scan</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Average Risk Meter */}
        <div className="p-4 bg-slate-950/60 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Average Churn Risk Score</span>
            <TrendingDown className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white font-mono">
              {metrics ? metrics.avg_risk_score : 0}
            </span>
            <span className="text-xs text-slate-500 font-mono">/ 100</span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2.5 overflow-hidden">
            <div
              className={`h-full rounded-full ${
                (metrics?.avg_risk_score || 0) >= 70
                  ? 'bg-rose-500'
                  : (metrics?.avg_risk_score || 0) >= 40
                  ? 'bg-amber-500'
                  : 'bg-emerald-500'
              }`}
              style={{ width: `${metrics?.avg_risk_score || 0}%` }}
            />
          </div>
        </div>

        {/* High Risk Count */}
        <div className="p-4 bg-slate-950/60 rounded-2xl border border-rose-900/40 bg-rose-950/10">
          <div className="flex items-center justify-between text-xs text-rose-300 mb-1">
            <span>High Risk Accounts</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-300 font-mono">
            {metrics?.high_risk_count || 0}
          </div>
          <p className="text-[10px] text-rose-400/80 mt-1 font-mono">Critical score &ge; 70</p>
        </div>

        {/* Medium Risk Count */}
        <div className="p-4 bg-slate-950/60 rounded-2xl border border-amber-900/40 bg-amber-950/10">
          <div className="flex items-center justify-between text-xs text-amber-300 mb-1">
            <span>Medium Risk Accounts</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-300 font-mono">
            {metrics?.medium_risk_count || 0}
          </div>
          <p className="text-[10px] text-amber-400/80 mt-1 font-mono">Warning score 40-69</p>
        </div>

        {/* At-Risk MRR */}
        <div className="p-4 bg-slate-950/60 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>At-Risk Revenue Volume</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            ${Number(metrics?.at_risk_mrr || 0).toFixed(2)}
          </div>
          <p className="text-[10px] text-slate-500 mt-1 font-mono">Total analyzed: {metrics?.total_customers_analyzed || 0}</p>
        </div>
      </div>

      {/* Tier Filter Tabs */}
      <div className="flex items-center space-x-2 text-xs">
        {(['ALL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((tier) => (
          <button
            key={tier}
            onClick={() => setTierFilter(tier)}
            className={`px-3 py-1.5 rounded-lg font-semibold transition border ${
              tierFilter === tier
                ? tier === 'HIGH'
                  ? 'bg-rose-950 text-rose-200 border-rose-700 shadow-md shadow-rose-900/20'
                  : tier === 'MEDIUM'
                  ? 'bg-amber-950 text-amber-200 border-amber-700'
                  : 'bg-indigo-600 text-white border-indigo-500'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            {tier === 'ALL' ? 'All Customers' : `${tier} Risk`}
          </button>
        ))}
      </div>

      {/* At-Risk Accounts Table */}
      <div className="bg-slate-950/60 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs">Computing churn risk vectors...</div>
        ) : filteredCustomers.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">No customer risk profiles found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Active Subs</th>
                  <th className="py-3 px-4 text-right">Active MRR</th>
                  <th className="py-3 px-4">Churn Risk Score</th>
                  <th className="py-3 px-4 text-center">Risk Tier</th>
                  <th className="py-3 px-4">Primary Trigger Signal</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {filteredCustomers.map((cust) => {
                  const topSignal = cust.signals[0];
                  return (
                    <tr key={cust.customer_id} className="hover:bg-slate-900/40 transition">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-200">{cust.full_name}</div>
                        <div className="text-[10px] text-slate-500 font-mono">
                          {cust.customer_code} • {cust.email}
                        </div>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        {cust.active_subscriptions_count}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-white">
                        ${Number(cust.total_mrr).toFixed(2)}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono font-bold text-slate-200 w-6">
                            {cust.risk_score}
                          </span>
                          <div className="w-24 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                cust.risk_tier === 'HIGH'
                                  ? 'bg-rose-500'
                                  : cust.risk_tier === 'MEDIUM'
                                  ? 'bg-amber-500'
                                  : 'bg-emerald-500'
                              }`}
                              style={{ width: `${cust.risk_score}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            cust.risk_tier === 'HIGH'
                              ? 'bg-rose-950 text-rose-300 border-rose-800'
                              : cust.risk_tier === 'MEDIUM'
                              ? 'bg-amber-950 text-amber-300 border-amber-800'
                              : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                          }`}
                        >
                          {cust.risk_tier}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {topSignal ? (
                          <span className="text-[11px] text-slate-300 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded-md">
                            {topSignal.signal_name} (+{topSignal.weight}pts)
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[11px]">Normal Pattern</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleOpenProfile(cust.customer_id)}
                          className="px-2.5 py-1 rounded-lg bg-indigo-600/80 hover:bg-indigo-600 text-white text-[11px] font-medium transition flex items-center space-x-1 ml-auto"
                        >
                          <Eye className="w-3 h-3" />
                          <span>Inspect</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Customer Risk & Retention Playbook Modal */}
      {isModalOpen && selectedProfile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 space-y-5 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2.5">
                <Radar className="w-5 h-5 text-rose-400" />
                <div>
                  <h3 className="text-base font-bold text-white">
                    Risk Profile: {selectedProfile.full_name}
                  </h3>
                  <p className="text-xs text-slate-400">
                    {selectedProfile.customer_code} • {selectedProfile.email}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                &times;
              </button>
            </div>

            {/* Risk Score & Playbook Card */}
            <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-slate-400">Calculated Risk Score:</span>
                  <span className="font-mono font-bold text-base text-white">
                    {selectedProfile.risk_score} / 100
                  </span>
                </div>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    selectedProfile.risk_tier === 'HIGH'
                      ? 'bg-rose-950 text-rose-300 border-rose-800'
                      : selectedProfile.risk_tier === 'MEDIUM'
                      ? 'bg-amber-950 text-amber-300 border-amber-800'
                      : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                  }`}
                >
                  {selectedProfile.risk_tier} RISK
                </span>
              </div>
              <div className="text-xs text-indigo-300 font-medium">
                <strong>Recommended Playbook:</strong> {selectedProfile.suggested_retention_playbook}
              </div>
            </div>

            {/* Contributing Risk Signals Breakdown */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Contributing Risk Factors & Heuristic Signals
              </h4>
              <div className="space-y-2">
                {selectedProfile.signals.length === 0 ? (
                  <div className="p-3 bg-slate-950/50 rounded-lg text-slate-500 text-xs">
                    No active risk signals detected. Account healthy.
                  </div>
                ) : (
                  selectedProfile.signals.map((sig) => (
                    <div
                      key={sig.signal_key}
                      className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200">{sig.signal_name}</span>
                        <span
                          className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            sig.severity === 'CRITICAL'
                              ? 'bg-rose-950 text-rose-300'
                              : sig.severity === 'WARNING'
                              ? 'bg-amber-950 text-amber-300'
                              : 'bg-blue-950 text-blue-300'
                          }`}
                        >
                          +{sig.weight} pts
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px]">{sig.description}</p>
                      <p className="text-emerald-400/90 text-[11px] italic">
                        &rarr; {sig.recommended_action}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Execute Retention Intervention */}
            <form onSubmit={handleRetentionSubmit} className="space-y-3 pt-2 border-t border-slate-800">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>Log Retention Intervention</span>
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1">Intervention Type</label>
                  <select
                    value={actionType}
                    onChange={(e) => setActionType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="DISCOUNT_OFFER">Special Retention Discount</option>
                    <option value="PLAN_CONSULTATION">Plan Optimization Consultation</option>
                    <option value="SUPPORT_OUTREACH">Executive Support Outreach</option>
                    <option value="PAUSE_EXTENDED">Extended Grace Period</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Discount % Offered</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={discountPercent}
                    onChange={(e) => setDiscountPercent(parseInt(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 text-xs mb-1">Intervention Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Details of offer or conversation with customer..."
                  rows={2}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition flex items-center space-x-1.5 disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{actionLoading ? 'Recording...' : 'Record Retention Action'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
