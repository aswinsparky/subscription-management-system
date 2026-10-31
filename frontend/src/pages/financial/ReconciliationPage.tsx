import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { 
  Scale, 
  AlertCircle, 
  Clock, 
  CheckCheck, 
  RefreshCw,
  FileCheck
} from 'lucide-react';

interface ReconciliationItem {
  id: number;
  payment_id: number | null;
  invoice_id: number | null;
  status: string;
  invoice_total: number;
  payment_amount: number;
  discrepancy_amount: number;
  notes: string | null;
  reconciled_at: string;
}

interface ReconciliationListResponse {
  items: ReconciliationItem[];
  total: number;
  unmatched_count: number;
  discrepancy_count: number;
  resolved_count: number;
}

export function ReconciliationPage() {
  const [data, setData] = useState<ReconciliationListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState<number | null>(null);
  const [resolveNotes, setResolveNotes] = useState('');

  const fetchReconciliation = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<ReconciliationListResponse>('/reconciliation');
      setData(res.data);
    } catch (err) {
      console.error('Failed to load reconciliations', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReconciliation();
  }, []);

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvingId) return;

    try {
      await apiClient.post(`/reconciliation/${resolvingId}/resolve`, {
        status: 'RESOLVED',
        notes: resolveNotes,
      });
      setResolvingId(null);
      setResolveNotes('');
      fetchReconciliation();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to resolve reconciliation');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'MATCHED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">MATCHED</span>;
      case 'PARTIALLY_MATCHED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">PARTIAL</span>;
      case 'DISCREPANCY':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 animate-pulse">DISCREPANCY</span>;
      case 'RESOLVED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">RESOLVED</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">UNMATCHED</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950/70 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <h2 className="text-xl font-extrabold text-white flex items-center space-x-2">
            <Scale className="w-5 h-5 text-indigo-400" />
            <span>Payment Reconciliation Engine</span>
          </h2>
          <p className="text-slate-400 text-xs mt-0.5">
            Audit payment receipts against invoice balances, detect discrepancies, and record resolution trails.
          </p>
        </div>
        <button
          onClick={fetchReconciliation}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Audit</span>
        </button>
      </div>

      {/* KPI Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Total Audited</div>
            <div className="text-xl font-black text-white">{data?.total || 0}</div>
          </div>
          <FileCheck className="w-5 h-5 text-indigo-400" />
        </div>
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Discrepancies</div>
            <div className="text-xl font-black text-rose-400">{data?.discrepancy_count || 0}</div>
          </div>
          <AlertCircle className="w-5 h-5 text-rose-400" />
        </div>
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Unmatched Payments</div>
            <div className="text-xl font-black text-amber-400">{data?.unmatched_count || 0}</div>
          </div>
          <Clock className="w-5 h-5 text-amber-400" />
        </div>
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400">Resolved Audit Trails</div>
            <div className="text-xl font-black text-emerald-400">{data?.resolved_count || 0}</div>
          </div>
          <CheckCheck className="w-5 h-5 text-emerald-400" />
        </div>
      </div>

      {/* Reconciliation Table */}
      <div className="bg-slate-950/60 rounded-2xl border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-5 py-3.5">Recon ID</th>
                <th className="px-5 py-3.5">Payment Ref</th>
                <th className="px-5 py-3.5">Invoice #</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5 text-right">Invoice ($)</th>
                <th className="px-5 py-3.5 text-right">Payment ($)</th>
                <th className="px-5 py-3.5 text-right">Discrepancy ($)</th>
                <th className="px-5 py-3.5">Audit Notes</th>
                <th className="px-5 py-3.5 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {data && data.items.length > 0 ? (
                data.items.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-900/50 transition">
                    <td className="px-5 py-3.5 font-mono text-slate-400">#{r.id}</td>
                    <td className="px-5 py-3.5 font-mono text-indigo-400 font-medium">
                      {r.payment_id ? `PAY #${r.payment_id}` : 'Unlinked'}
                    </td>
                    <td className="px-5 py-3.5 font-mono text-slate-300">
                      {r.invoice_id ? `INV #${r.invoice_id}` : 'Unassigned'}
                    </td>
                    <td className="px-5 py-3.5">{getStatusBadge(r.status)}</td>
                    <td className="px-5 py-3.5 text-right font-mono text-slate-300 font-medium">
                      ${Number(r.invoice_total).toFixed(2)}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono text-emerald-400 font-medium">
                      ${Number(r.payment_amount).toFixed(2)}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono font-bold text-rose-400">
                      ${Number(r.discrepancy_amount).toFixed(2)}
                    </td>
                    <td className="px-5 py-3.5 text-slate-400 max-w-xs truncate text-[11px]">
                      {r.notes || '—'}
                    </td>
                    <td className="px-5 py-3.5 text-center">
                      {r.status !== 'RESOLVED' && r.status !== 'MATCHED' && (
                        <button
                          onClick={() => setResolvingId(r.id)}
                          className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg text-xs transition"
                        >
                          Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="px-5 py-8 text-center text-slate-500">
                    {loading ? 'Auditing records...' : 'All payments and invoices are cleanly reconciled.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Resolution Modal */}
      {resolvingId && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">Resolve Reconciliation Discrepancy</h3>
            <form onSubmit={handleResolve} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Resolution Explanation & Notes</label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Verified with banking portal statement; settled discrepancy note"
                  value={resolveNotes}
                  onChange={(e) => setResolveNotes(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                ></textarea>
              </div>
              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setResolvingId(null)}
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

