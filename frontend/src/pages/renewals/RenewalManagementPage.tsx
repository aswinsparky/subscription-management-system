import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { DueSubscription, RenewalBillingRequest, BatchRenewalResult } from '../../types/renewal';
import { 
  RefreshCw, 
  Play, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  DollarSign, 
  Key, 
  ExternalLink,
  Zap
} from 'lucide-react';

export const RenewalManagementPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'due' | 'requests'>('due');
  const [dueList, setDueList] = useState<DueSubscription[]>([]);
  const [requests, setRequests] = useState<RenewalBillingRequest[]>([]);
  const [horizonDays, setHorizonDays] = useState<number>(7);
  const [loading, setLoading] = useState<boolean>(true);
  const [batchLoading, setBatchLoading] = useState<boolean>(false);
  const [lastBatchResult, setLastBatchResult] = useState<BatchRenewalResult | null>(null);

  const fetchDueSubscriptions = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<DueSubscription[]>('/renewals/due', {
        params: { horizon_days: horizonDays },
      });
      setDueList(res.data);
    } catch (err) {
      console.error('Failed to load due subscriptions', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRenewalRequests = async () => {
    try {
      const res = await apiClient.get('/renewals/requests', {
        params: { page: 1, size: 50 },
      });
      setRequests(res.data.items || []);
    } catch (err) {
      console.error('Failed to load renewal requests', err);
    }
  };

  useEffect(() => {
    fetchDueSubscriptions();
    fetchRenewalRequests();
  }, [horizonDays]);

  const handleTriggerSingle = async (subId: number) => {
    try {
      await apiClient.post(`/renewals/trigger/${subId}`);
      await Promise.all([fetchDueSubscriptions(), fetchRenewalRequests()]);
      alert('Subscription renewal successfully triggered!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to trigger renewal.');
    }
  };

  const handleBatchRun = async () => {
    try {
      setBatchLoading(true);
      const res = await apiClient.post<BatchRenewalResult>('/renewals/batch-run', null, {
        params: { horizon_days: 0 },
      });
      setLastBatchResult(res.data);
      await Promise.all([fetchDueSubscriptions(), fetchRenewalRequests()]);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to run batch renewals.');
    } finally {
      setBatchLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Quick Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-950/60 p-6 rounded-2xl border border-slate-800">
        <div>
          <div className="flex items-center space-x-2.5 text-indigo-400 mb-1">
            <RefreshCw className="w-5 h-5" />
            <h2 className="text-xl font-bold text-white tracking-wide">
              Automated Renewal Scheduler & Invoicing Engine
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            Idempotent automated renewal execution, period advancement, and automated invoice generation.
          </p>
        </div>

        <button
          onClick={handleBatchRun}
          disabled={batchLoading}
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50 self-start md:self-auto"
        >
          <Zap className="w-4 h-4 text-amber-300" />
          <span>{batchLoading ? 'Executing Batch...' : 'Run Automated Renewal Cycle'}</span>
        </button>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-950/60 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Subscriptions Due (&le; {horizonDays}d)</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{dueList.length}</div>
        </div>

        <div className="p-4 bg-slate-950/60 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Processed Billing Requests</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-300 font-mono">
            {requests.filter((r) => r.status === 'PROCESSED').length}
          </div>
        </div>

        <div className="p-4 bg-slate-950/60 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Pending Recurring Invoices</span>
            <RefreshCw className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-indigo-300 font-mono">
            {requests.filter((r) => r.status === 'PENDING').length}
          </div>
        </div>

        <div className="p-4 bg-slate-950/60 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Total Renewed Revenue</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            $
            {requests
              .filter((r) => r.status === 'PROCESSED')
              .reduce((sum, r) => sum + Number(r.amount), 0)
              .toFixed(2)}
          </div>
        </div>
      </div>

      {/* Batch Run Notification Banner */}
      {lastBatchResult && (
        <div className="p-4 bg-indigo-950/40 border border-indigo-800/60 rounded-xl text-xs flex items-center justify-between text-indigo-200">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>
              Batch Cycle Completed: <strong>{lastBatchResult.processed_count}</strong> subscriptions processed,{' '}
              <strong>{lastBatchResult.failed_count}</strong> failed out of {lastBatchResult.total_due} due.
            </span>
          </div>
          <button
            onClick={() => setLastBatchResult(null)}
            className="text-slate-400 hover:text-white font-bold"
          >
            &times;
          </button>
        </div>
      )}

      {/* Module Tabs & Horizon Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab('due')}
            className={`px-4 py-2 rounded-xl font-bold transition border ${
              activeTab === 'due'
                ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/20'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            Due Subscriptions ({dueList.length})
          </button>
          <button
            onClick={() => setActiveTab('requests')}
            className={`px-4 py-2 rounded-xl font-bold transition border ${
              activeTab === 'requests'
                ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/20'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            Billing Requests Ledger ({requests.length})
          </button>
        </div>

        {activeTab === 'due' && (
          <div className="flex items-center space-x-2">
            <span className="text-slate-400">Horizon:</span>
            {[0, 3, 7, 14, 30].map((days) => (
              <button
                key={days}
                onClick={() => setHorizonDays(days)}
                className={`px-2.5 py-1 rounded-lg font-mono text-[11px] border ${
                  horizonDays === days
                    ? 'bg-indigo-950 text-indigo-300 border-indigo-700'
                    : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                {days === 0 ? 'Today' : `${days}d`}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Table Render */}
      <div className="bg-slate-950/60 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        {activeTab === 'due' ? (
          loading ? (
            <div className="p-12 text-center text-slate-500 text-xs">Scanning for due subscriptions...</div>
          ) : dueList.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              No active subscriptions due for renewal within the selected {horizonDays}-day horizon.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Subscription</th>
                    <th className="py-3 px-4">Customer</th>
                    <th className="py-3 px-4">Plan & Interval</th>
                    <th className="py-3 px-4">Due Date</th>
                    <th className="py-3 px-4">Idempotency Key</th>
                    <th className="py-3 px-4 text-right">Renewal Amount</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {dueList.map((item) => (
                    <tr key={item.subscription_id} className="hover:bg-slate-900/40 transition">
                      <td className="py-3 px-4 font-mono font-semibold text-indigo-300">
                        {item.subscription_number}
                      </td>
                      <td className="py-3 px-4 text-slate-200 font-medium">
                        {item.customer_name}
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-slate-300">{item.plan_name}</span>
                        <span className="ml-2 text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                          {item.billing_interval}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        {new Date(item.next_billing_date).toLocaleDateString()}
                        <span
                          className={`ml-2 text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            item.days_until_due <= 0
                              ? 'bg-rose-950 text-rose-300 border border-rose-800'
                              : 'bg-amber-950 text-amber-300 border border-amber-800'
                          }`}
                        >
                          {item.days_until_due <= 0 ? 'DUE NOW' : `in ${item.days_until_due}d`}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                        <div className="flex items-center space-x-1">
                          <Key className="w-3 h-3 text-indigo-400 flex-shrink-0" />
                          <span className="truncate max-w-[180px]">{item.idempotency_key}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-white">
                        ${Number(item.amount).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleTriggerSingle(item.subscription_id)}
                          className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition flex items-center space-x-1 text-[11px] ml-auto shadow-md shadow-indigo-600/20"
                        >
                          <Play className="w-3 h-3" />
                          <span>Renew</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : (
          /* Billing Requests Ledger Tab */
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Request ID</th>
                  <th className="py-3 px-4">Idempotency Key</th>
                  <th className="py-3 px-4">Subscription</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Period</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4">Generated Invoice Ref</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {requests.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-900/40 transition">
                    <td className="py-3 px-4 font-mono font-bold text-slate-400">
                      #{req.id}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-indigo-300">
                      {req.idempotency_key}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-200">
                      {req.subscription_number || `Sub #${req.subscription_id}`}
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-medium">
                      {req.customer_name || `Cust #${req.customer_id}`}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                      {new Date(req.billing_period_start).toLocaleDateString()} -{' '}
                      {new Date(req.billing_period_end).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-slate-100">
                      ${Number(req.amount).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {req.status === 'PROCESSED' ? (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Processed</span>
                        </span>
                      ) : req.status === 'PENDING' ? (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-950 text-amber-300 border border-amber-800">
                          <Clock className="w-3 h-3" />
                          <span>Pending M2</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-950 text-rose-300 border border-rose-800">
                          <AlertTriangle className="w-3 h-3" />
                          <span>Failed</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono font-semibold text-emerald-300">
                      {req.invoice_reference ? (
                        <div className="flex items-center space-x-1">
                          <span>{req.invoice_reference}</span>
                          <ExternalLink className="w-3 h-3 text-emerald-400" />
                        </div>
                      ) : (
                        <span className="text-slate-600">&mdash;</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
