import { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { 
  HeartHandshake, 
  RotateCw, 
  RefreshCw
} from 'lucide-react';

interface RecoveryAttempt {
  id: number;
  subscription_id: number;
  invoice_id: number | null;
  payment_id: number | null;
  failure_type: string;
  failure_reason: string;
  retry_count: number;
  max_retries: number;
  next_retry_at: string | null;
  recovery_status: string;
  idempotency_key: string;
  error_details: string | null;
  created_at: string;
}

export function BillingRecoveryPage() {
  const [attempts, setAttempts] = useState<RecoveryAttempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [retryingId, setRetryingId] = useState<number | null>(null);

  const fetchAttempts = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<RecoveryAttempt[]>('/billing-recovery');
      setAttempts(res.data);
    } catch (err) {
      console.error('Failed to load billing recovery attempts', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttempts();
  }, []);

  const handleManualRetry = async (attemptId: number) => {
    try {
      setRetryingId(attemptId);
      await apiClient.post('/billing-recovery/retry', { attempt_id: attemptId });
      await fetchAttempts();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to execute recovery retry');
    } finally {
      setRetryingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RECOVERED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">RECOVERED</span>;
      case 'RETRYING':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 animate-pulse">RETRYING</span>;
      case 'PENDING':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">PENDING</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">FAILED PERMANENTLY</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950/70 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-1.5 bg-emerald-500/20 text-emerald-400 rounded-lg">
              <HeartHandshake className="w-4 h-4" />
            </span>
            <span className="text-xs uppercase font-mono tracking-wider text-emerald-400 font-semibold">
              Self-Healing Automated Failure Recovery
            </span>
          </div>
          <h2 className="text-xl font-extrabold text-white mt-1">Self-Healing Billing (Module 11)</h2>
          <p className="text-slate-400 text-xs mt-0.5">
            Automatically recovers failed subscription invoice runs and payment transactions with exponential backoff.
          </p>
        </div>

        <button
          onClick={fetchAttempts}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Recovery Monitor</span>
        </button>
      </div>

      {/* Recovery Table */}
      <div className="bg-slate-950/60 rounded-2xl border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-5 py-3.5">Attempt ID</th>
                <th className="px-5 py-3.5">Subscription</th>
                <th className="px-5 py-3.5">Failure Type</th>
                <th className="px-5 py-3.5">Failure Reason</th>
                <th className="px-5 py-3.5">Retry Progress</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5">Audit Log</th>
                <th className="px-5 py-3.5 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {attempts.length > 0 ? (
                attempts.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-900/50 transition">
                    <td className="px-5 py-3.5 font-mono text-slate-400">#{a.id}</td>
                    <td className="px-5 py-3.5 font-mono text-indigo-400 font-semibold">
                      SUB #{a.subscription_id}
                    </td>
                    <td className="px-5 py-3.5 font-mono text-[11px] text-slate-300">
                      {a.failure_type}
                    </td>
                    <td className="px-5 py-3.5 text-slate-300 max-w-xs truncate">
                      {a.failure_reason}
                    </td>
                    <td className="px-5 py-3.5 font-mono text-slate-400">
                      {a.retry_count} / {a.max_retries}
                    </td>
                    <td className="px-5 py-3.5">{getStatusBadge(a.recovery_status)}</td>
                    <td className="px-5 py-3.5 text-slate-400 max-w-xs truncate text-[11px]">
                      {a.error_details || '—'}
                    </td>
                    <td className="px-5 py-3.5 text-center">
                      {a.recovery_status !== 'RECOVERED' && a.retry_count < a.max_retries && (
                        <button
                          onClick={() => handleManualRetry(a.id)}
                          disabled={retryingId === a.id}
                          className="flex items-center space-x-1 px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition disabled:opacity-50"
                        >
                          <RotateCw className={`w-3 h-3 ${retryingId === a.id ? 'animate-spin' : ''}`} />
                          <span>Retry Now</span>
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-5 py-8 text-center text-slate-500">
                    {loading ? 'Scanning recovery attempts...' : 'No failed billing operations currently require recovery.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
