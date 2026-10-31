import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { 
  ShieldAlert, 
  AlertTriangle, 
  ShieldCheck, 
  Play, 
  TrendingDown
} from 'lucide-react';

interface Finding {
  id: number;
  issue_code: string;
  issue_title: string;
  category: string;
  severity: string;
  customer_id: number | null;
  subscription_id: number | null;
  invoice_id: number | null;
  estimated_loss: number;
  explanation: string;
  recommended_action: string;
  resolution_status: string;
  detected_at: string;
  resolution_notes: string | null;
}

export function RevenueGuardianPage() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningAudit, setRunningAudit] = useState(false);
  const [statusFilter, setStatusFilter] = useState('OPEN');
  const [resolvingFinding, setResolvingFinding] = useState<Finding | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');

  const fetchFindings = async () => {
    try {
      setLoading(true);
      const url = statusFilter ? `/revenue-guardian/findings?status=${statusFilter}` : '/revenue-guardian/findings';
      const res = await apiClient.get<Finding[]>(url);
      setFindings(res.data);
    } catch (err) {
      console.error('Failed to load Revenue Guardian findings', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFindings();
  }, [statusFilter]);

  const handleRunAudit = async () => {
    try {
      setRunningAudit(true);
      await apiClient.post('/revenue-guardian/run');
      await fetchFindings();
    } catch (err) {
      alert('Failed to execute Revenue Guardian scan.');
    } finally {
      setRunningAudit(false);
    }
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvingFinding) return;

    try {
      await apiClient.post(`/revenue-guardian/findings/${resolvingFinding.id}/resolve`, {
        resolution_status: 'RESOLVED',
        resolution_notes: resolutionNotes,
      });
      setResolvingFinding(null);
      setResolutionNotes('');
      fetchFindings();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to resolve finding');
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">MEDIUM</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-500/20 text-slate-400 border border-slate-500/30">LOW</span>;
    }
  };

  const totalLeakageAtRisk = findings.reduce((acc, f) => acc + (f.resolution_status === 'OPEN' ? Number(f.estimated_loss) : 0), 0);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-rose-950/40 via-slate-950/70 to-slate-950/70 p-6 rounded-2xl border border-rose-900/30 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-1.5 bg-rose-500/20 text-rose-400 rounded-lg">
              <ShieldAlert className="w-4 h-4" />
            </span>
            <span className="text-xs uppercase font-mono tracking-wider text-rose-400 font-semibold">
              Deterministic Anomaly Detection Engine
            </span>
          </div>
          <h2 className="text-xl font-extrabold text-white mt-1">Revenue Guardian</h2>
          <p className="text-slate-400 text-xs mt-0.5">
            Continuously monitors billing cycles, uncollected invoices, calculation mismatches, and prevents financial leakage.
          </p>
        </div>

        <button
          onClick={handleRunAudit}
          disabled={runningAudit}
          className="flex items-center space-x-2 px-5 py-2.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-rose-600/30 transition disabled:opacity-50"
        >
          <Play className={`w-3.5 h-3.5 ${runningAudit ? 'animate-spin' : ''}`} />
          <span>{runningAudit ? 'Auditing Database...' : 'Run Live Revenue Audit'}</span>
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Total Findings (Filtered)</div>
            <div className="text-2xl font-black text-white">{findings.length}</div>
          </div>
          <AlertTriangle className="w-5 h-5 text-indigo-400" />
        </div>
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Total Estimated Leakage</div>
            <div className="text-2xl font-black text-rose-400 font-mono">
              ${totalLeakageAtRisk.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </div>
          <TrendingDown className="w-5 h-5 text-rose-400" />
        </div>
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Status Filter</div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 mt-1"
            >
              <option value="">All Findings</option>
              <option value="OPEN">Open Anomalies</option>
              <option value="RESOLVED">Resolved Findings</option>
            </select>
          </div>
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
        </div>
      </div>

      {/* Findings Cards List */}
      <div className="space-y-4">
        {findings.length > 0 ? (
          findings.map((f) => (
            <div
              key={f.id}
              className="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-5 shadow-lg hover:border-slate-700 transition space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center space-x-3">
                  {getSeverityBadge(f.severity)}
                  <span className="font-mono text-xs text-slate-400">[{f.issue_code}]</span>
                  <h3 className="font-bold text-sm text-white">{f.issue_title}</h3>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-rose-400">
                    Impact: ${Number(f.estimated_loss).toFixed(2)}
                  </span>
                  {f.resolution_status === 'OPEN' ? (
                    <button
                      onClick={() => setResolvingFinding(f)}
                      className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition"
                    >
                      Resolve Issue
                    </button>
                  ) : (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      RESOLVED
                    </span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs bg-slate-900/60 p-3.5 rounded-xl border border-slate-800/50">
                <div>
                  <span className="text-slate-400 font-semibold block mb-0.5">Explanation:</span>
                  <p className="text-slate-300 leading-relaxed">{f.explanation}</p>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold block mb-0.5">Recommended Action:</span>
                  <p className="text-indigo-300 leading-relaxed">{f.recommended_action}</p>
                </div>
              </div>

              {f.resolution_notes && (
                <div className="text-[11px] text-emerald-400 bg-emerald-950/20 border border-emerald-900/30 p-2.5 rounded-lg">
                  <b>Resolution Note:</b> {f.resolution_notes}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="bg-slate-950/40 border border-slate-800 rounded-2xl p-12 text-center text-slate-500">
            {loading ? 'Scanning for financial anomalies...' : 'Zero revenue leakage detected! All subscription billing and invoices are consistent.'}
          </div>
        )}
      </div>

      {/* Resolution Modal */}
      {resolvingFinding && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">Resolve Revenue Leakage Finding</h3>
            <p className="text-xs text-slate-400">{resolvingFinding.issue_title}</p>
            <form onSubmit={handleResolve} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Audit Resolution Notes</label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Manually verified and generated missing invoice #INV-2026-00003."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                ></textarea>
              </div>
              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setResolvingFinding(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl transition"
                >
                  Confirm Resolution
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

