import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { Subscription, SubscriptionStatus, SubscriptionEvent } from '../../types/subscription';
import { Customer } from '../../types/customer';
import { Product } from '../../types/product';
import { Plan } from '../../types/plan';
import { 
  Repeat, 
  Plus, 
  CheckCircle, 
  Play, 
  Pause, 
  XCircle, 
  Clock, 
  History, 
  Eye, 
  AlertCircle,
  Layers,
  ArrowRight
} from 'lucide-react';

export const SubscriptionListPage: React.FC = () => {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Details & Time Machine Modal
  const [selectedSub, setSelectedSub] = useState<Subscription | null>(null);
  const [subEvents, setSubEvents] = useState<SubscriptionEvent[]>([]);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  // Action Reason Modal (Pause / Cancel)
  const [actionTarget, setActionTarget] = useState<{ id: number; action: 'pause' | 'cancel' } | null>(null);
  const [actionReason, setActionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Create Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | ''>('');
  const [selectedPlanId, setSelectedPlanId] = useState<number | ''>('');
  const [orderLines, setOrderLines] = useState<
    Array<{ product_id: number; variant_id?: number; quantity: number }>
  >([{ product_id: 0, quantity: 1 }]);

  const fetchSubscriptions = async () => {
    try {
      setLoading(true);
      const params: any = { page: 1, size: 50 };
      if (statusFilter !== 'ALL') {
        params.status = statusFilter;
      }
      const res = await apiClient.get('/subscriptions', { params });
      setSubscriptions(res.data.items);
      setTotal(res.data.total);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch subscriptions.');
    } finally {
      setLoading(false);
    }
  };

  const loadDependencies = async () => {
    try {
      const [custRes, prodRes, planRes] = await Promise.all([
        apiClient.get('/customers', { params: { size: 100 } }),
        apiClient.get('/products', { params: { size: 100 } }),
        apiClient.get('/plans', { params: { size: 100 } }),
      ]);
      setCustomers(custRes.data.items || custRes.data || []);
      setProducts(prodRes.data.items || prodRes.data || []);
      setPlans(planRes.data.items || planRes.data || []);
    } catch (err) {
      console.error('Failed to load dependencies', err);
    }
  };

  useEffect(() => {
    fetchSubscriptions();
  }, [statusFilter]);

  useEffect(() => {
    loadDependencies();
  }, []);

  const handleOpenDetails = async (sub: Subscription) => {
    setSelectedSub(sub);
    setIsDetailsOpen(true);
    try {
      const res = await apiClient.get(`/subscriptions/${sub.id}/events`);
      setSubEvents(res.data);
    } catch {
      setSubEvents(sub.events || []);
    }
  };

  const handleExecuteTransition = async (id: number, transition: 'confirm' | 'activate' | 'close') => {
    try {
      await apiClient.post(`/subscriptions/${id}/${transition}`);
      await fetchSubscriptions();
      if (selectedSub && selectedSub.id === id) {
        const updated = await apiClient.get(`/subscriptions/${id}`);
        setSelectedSub(updated.data);
        const events = await apiClient.get(`/subscriptions/${id}/events`);
        setSubEvents(events.data);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || `Failed to ${transition} subscription.`);
    }
  };

  const handleActionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionTarget) return;
    try {
      setActionLoading(true);
      await apiClient.post(`/subscriptions/${actionTarget.id}/${actionTarget.action}`, {
        reason: actionReason || undefined,
      });
      setActionTarget(null);
      setActionReason('');
      await fetchSubscriptions();
    } catch (err: any) {
      alert(err.response?.data?.detail || `Failed to ${actionTarget.action} subscription.`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateSubscription = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomerId || !selectedPlanId) {
      alert('Please select both Customer and Plan.');
      return;
    }
    const validLines = orderLines.filter((l) => l.product_id > 0 && l.quantity > 0);
    if (validLines.length === 0) {
      alert('Please add at least one product line.');
      return;
    }

    try {
      await apiClient.post('/subscriptions', {
        customer_id: Number(selectedCustomerId),
        plan_id: Number(selectedPlanId),
        items: validLines,
      });
      setIsCreateOpen(false);
      setSelectedCustomerId('');
      setSelectedPlanId('');
      setOrderLines([{ product_id: 0, quantity: 1 }]);
      await fetchSubscriptions();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create subscription.');
    }
  };

  const getStatusBadge = (status: SubscriptionStatus) => {
    switch (status) {
      case 'ACTIVE':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800">
            <Play className="w-3 h-3" />
            <span>Active</span>
          </span>
        );
      case 'CONFIRMED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-950 text-blue-300 border border-blue-800">
            <CheckCircle className="w-3 h-3" />
            <span>Confirmed</span>
          </span>
        );
      case 'PAUSED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950 text-amber-300 border border-amber-800">
            <Pause className="w-3 h-3" />
            <span>Paused</span>
          </span>
        );
      case 'DRAFT':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
            <Clock className="w-3 h-3" />
            <span>Draft</span>
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950 text-rose-300 border border-rose-800">
            <XCircle className="w-3 h-3" />
            <span>Cancelled</span>
          </span>
        );
      case 'CLOSED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-900 text-slate-400 border border-slate-700">
            <span>Closed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400">
            <span>{status}</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Quick Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-950/60 p-6 rounded-2xl border border-slate-800">
        <div>
          <div className="flex items-center space-x-2.5 text-indigo-400 mb-1">
            <Repeat className="w-5 h-5" />
            <h2 className="text-xl font-bold text-white tracking-wide">
              Subscription Lifecycle & State Machine
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            Strict policy-checked state machine: Draft &rarr; Confirmed &rarr; Active &harr; Paused &rarr; Closed/Cancelled.
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 transition self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>New Subscription</span>
        </button>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
        {['ALL', 'ACTIVE', 'CONFIRMED', 'PAUSED', 'DRAFT', 'CLOSED', 'CANCELLED'].map((tab) => (
          <button
            key={tab}
            onClick={() => setStatusFilter(tab)}
            className={`px-3 py-1.5 rounded-lg font-semibold transition border ${
              statusFilter === tab
                ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/20'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Subscriptions Table */}
      <div className="bg-slate-950/60 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400">
            Total Subscriptions: <strong className="text-white">{total}</strong>
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-500 text-sm">Loading subscriptions...</div>
        ) : error ? (
          <div className="p-6 text-rose-400 text-sm flex items-center space-x-2">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        ) : subscriptions.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-sm">
            No subscriptions found matching the filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Sub Number</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Plan & Interval</th>
                  <th className="py-3 px-4">Next Billing</th>
                  <th className="py-3 px-4 text-right">Total Amount</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Lifecycle Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {subscriptions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-900/40 transition">
                    <td className="py-3 px-4 font-mono font-semibold text-indigo-300">
                      {sub.subscription_number}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-200">
                        {sub.customer?.full_name || `Customer #${sub.customer_id}`}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        {sub.customer?.email}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="text-slate-200 font-medium">
                        {sub.plan?.name || `Plan #${sub.plan_id}`}
                      </div>
                      <span className="inline-block text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                        {sub.billing_interval}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-mono text-[11px]">
                      {new Date(sub.next_billing_date).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-slate-100">
                      ${Number(sub.total_amount).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {getStatusBadge(sub.status)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center space-x-1.5">
                        <button
                          onClick={() => handleOpenDetails(sub)}
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition flex items-center space-x-1 text-[11px]"
                          title="View Details & Time Machine"
                        >
                          <Eye className="w-3 h-3" />
                          <span>Timeline</span>
                        </button>

                        {/* Transition Action Buttons */}
                        {(sub.status === 'DRAFT' || sub.status === 'QUOTATION') && (
                          <button
                            onClick={() => handleExecuteTransition(sub.id, 'confirm')}
                            className="px-2 py-1 rounded bg-blue-900/60 hover:bg-blue-800 text-blue-200 border border-blue-700 transition flex items-center space-x-1 text-[11px]"
                            title="Confirm Subscription"
                          >
                            <CheckCircle className="w-3 h-3" />
                            <span>Confirm</span>
                          </button>
                        )}

                        {sub.status === 'CONFIRMED' && (
                          <button
                            onClick={() => handleExecuteTransition(sub.id, 'activate')}
                            className="px-2 py-1 rounded bg-emerald-900/60 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 transition flex items-center space-x-1 text-[11px]"
                            title="Activate Subscription"
                          >
                            <Play className="w-3 h-3" />
                            <span>Activate</span>
                          </button>
                        )}

                        {sub.status === 'ACTIVE' && (
                          <>
                            <button
                              onClick={() => setActionTarget({ id: sub.id, action: 'pause' })}
                              className="px-2 py-1 rounded bg-amber-900/60 hover:bg-amber-800 text-amber-200 border border-amber-700 transition flex items-center space-x-1 text-[11px]"
                              title="Pause Subscription"
                            >
                              <Pause className="w-3 h-3" />
                              <span>Pause</span>
                            </button>
                            <button
                              onClick={() => handleExecuteTransition(sub.id, 'close')}
                              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition text-[11px]"
                              title="Close normally"
                            >
                              <span>Close</span>
                            </button>
                          </>
                        )}

                        {sub.status === 'PAUSED' && (
                          <button
                            onClick={() => handleExecuteTransition(sub.id, 'activate')}
                            className="px-2 py-1 rounded bg-emerald-900/60 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 transition flex items-center space-x-1 text-[11px]"
                            title="Resume Subscription"
                          >
                            <Play className="w-3 h-3" />
                            <span>Resume</span>
                          </button>
                        )}

                        {(sub.status === 'ACTIVE' || sub.status === 'PAUSED') && (
                          <button
                            onClick={() => setActionTarget({ id: sub.id, action: 'cancel' })}
                            className="px-2 py-1 rounded bg-rose-950 hover:bg-rose-900 text-rose-300 border border-rose-800 transition flex items-center space-x-1 text-[11px]"
                            title="Cancel Subscription"
                          >
                            <XCircle className="w-3 h-3" />
                            <span>Cancel</span>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Details & Event Ledger Modal */}
      {isDetailsOpen && selectedSub && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl p-6 space-y-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-3">
                <div className="bg-indigo-600/20 text-indigo-400 p-2 rounded-xl border border-indigo-500/30">
                  <Repeat className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                    <span>Subscription {selectedSub.subscription_number}</span>
                    {getStatusBadge(selectedSub.status)}
                  </h3>
                  <p className="text-xs text-slate-400">
                    Customer: {selectedSub.customer?.full_name} ({selectedSub.customer?.customer_code})
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsDetailsOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                &times;
              </button>
            </div>

            {/* Info Cards Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Plan</span>
                <span className="font-semibold text-white">{selectedSub.plan?.name}</span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Billing Interval</span>
                <span className="font-semibold text-white font-mono">{selectedSub.billing_interval}</span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Current Period</span>
                <span className="font-semibold text-slate-300 font-mono text-[11px]">
                  {new Date(selectedSub.current_period_start).toLocaleDateString()} -{' '}
                  {new Date(selectedSub.current_period_end).toLocaleDateString()}
                </span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1">Total Amount</span>
                <span className="font-bold text-indigo-300 font-mono text-sm">
                  ${Number(selectedSub.total_amount).toFixed(2)}
                </span>
              </div>
            </div>

            {/* Subscription Line Items */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                <Layers className="w-3.5 h-3.5 text-indigo-400" />
                <span>Line Items</span>
              </h4>
              <div className="bg-slate-950/40 rounded-xl border border-slate-800/80 overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/60 text-slate-400 font-mono uppercase">
                    <tr>
                      <th className="py-2.5 px-3">Product / Variant</th>
                      <th className="py-2.5 px-3 text-center">Qty</th>
                      <th className="py-2.5 px-3 text-right">Unit Price</th>
                      <th className="py-2.5 px-3 text-right">Subtotal</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {selectedSub.items?.map((item) => (
                      <tr key={item.id}>
                        <td className="py-2.5 px-3">
                          <span className="font-medium text-slate-200">
                            {item.product_name || `Product #${item.product_id}`}
                          </span>
                          {item.variant_name && (
                            <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 border border-slate-700">
                              {item.variant_name}
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-center font-mono">{item.quantity}</td>
                        <td className="py-2.5 px-3 text-right font-mono">
                          ${Number(item.unit_price).toFixed(2)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-200">
                          ${Number(item.subtotal).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Append-Only Event Ledger (Time Machine) */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                <History className="w-3.5 h-3.5 text-indigo-400" />
                <span>Audit Event Ledger (Append-Only Time Machine)</span>
              </h4>
              <div className="space-y-2 max-h-56 overflow-y-auto">
                {subEvents.length === 0 ? (
                  <div className="p-4 text-center text-slate-500 text-xs">No events recorded.</div>
                ) : (
                  subEvents.map((evt) => (
                    <div
                      key={evt.id}
                      className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/70 text-xs flex items-start justify-between gap-4"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono font-bold text-indigo-400">
                            {evt.event_type}
                          </span>
                          <span className="text-[10px] text-slate-400">
                            by {evt.actor_email || 'System'} ({evt.actor_role})
                          </span>
                        </div>
                        {evt.reason && (
                          <p className="text-slate-300 italic text-[11px]">
                            &ldquo;{evt.reason}&rdquo;
                          </p>
                        )}
                        {evt.previous_state && (
                          <div className="flex items-center space-x-1.5 text-[10px] font-mono text-slate-400 mt-1">
                            <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                              {evt.previous_state.status}
                            </span>
                            <ArrowRight className="w-2.5 h-2.5" />
                            <span className="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                              {evt.new_state?.status}
                            </span>
                          </div>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono whitespace-nowrap">
                        {new Date(evt.created_at).toLocaleString()}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-800">
              <button
                onClick={() => setIsDetailsOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Action Reason Modal (Pause / Cancel) */}
      {actionTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <form
            onSubmit={handleActionSubmit}
            className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl"
          >
            <h3 className="text-base font-bold text-white capitalize">
              {actionTarget.action} Subscription
            </h3>
            <p className="text-xs text-slate-400">
              Please enter an audit reason for this state transition. This will be permanently written to the immutable event ledger.
            </p>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Reason</label>
              <textarea
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                placeholder={`Reason for ${actionTarget.action}...`}
                rows={3}
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="flex justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setActionTarget(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Dismiss
              </button>
              <button
                type="submit"
                disabled={actionLoading}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition disabled:opacity-50"
              >
                {actionLoading ? 'Processing...' : 'Confirm'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Create Subscription Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
          <form
            onSubmit={handleCreateSubscription}
            className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 space-y-5 shadow-2xl my-8"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <Plus className="w-4 h-4 text-indigo-400" />
                <span>Create New Subscription</span>
              </h3>
              <button
                type="button"
                onClick={() => setIsCreateOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                &times;
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Customer</label>
                <select
                  value={selectedCustomerId}
                  onChange={(e) => setSelectedCustomerId(e.target.value ? Number(e.target.value) : '')}
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Select customer...</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.full_name} ({c.customer_code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Subscription Plan</label>
                <select
                  value={selectedPlanId}
                  onChange={(e) => setSelectedPlanId(e.target.value ? Number(e.target.value) : '')}
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Select plan...</option>
                  {plans.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.billing_interval}) - ${Number(p.plan_price).toFixed(2)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Line Items */}
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Product Items
                </label>
                <button
                  type="button"
                  onClick={() => setOrderLines([...orderLines, { product_id: 0, quantity: 1 }])}
                  className="text-indigo-400 hover:text-indigo-300 text-xs font-semibold flex items-center space-x-1"
                >
                  <Plus className="w-3 h-3" />
                  <span>Add Line</span>
                </button>
              </div>

              {orderLines.map((line, idx) => {
                const prod = products.find((p) => p.id === line.product_id);
                return (
                  <div
                    key={idx}
                    className="grid grid-cols-12 gap-2 items-center bg-slate-950/60 p-2.5 rounded-xl border border-slate-800 text-xs"
                  >
                    <div className="col-span-6">
                      <select
                        value={line.product_id}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          const updated = [...orderLines];
                          updated[idx].product_id = val;
                          updated[idx].variant_id = undefined;
                          setOrderLines(updated);
                        }}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                      >
                        <option value={0}>Select product...</option>
                        {products.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name} (${Number(p.sales_price).toFixed(2)})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="col-span-3">
                      {prod && prod.variants && prod.variants.length > 0 ? (
                        <select
                          value={line.variant_id || ''}
                          onChange={(e) => {
                            const val = e.target.value ? Number(e.target.value) : undefined;
                            const updated = [...orderLines];
                            updated[idx].variant_id = val;
                            setOrderLines(updated);
                          }}
                          className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                        >
                          <option value="">Standard (No Variant)</option>
                          {prod.variants.map((v) => (
                            <option key={v.id} value={v.id}>
                              {v.variant_name} (+${Number(v.additional_price).toFixed(2)})
                            </option>
                          ))}
                        </select>
                      ) : (
                        <div className="text-slate-500 font-mono text-[11px] p-2">Standard</div>
                      )}
                    </div>

                    <div className="col-span-2">
                      <input
                        type="number"
                        min="1"
                        value={line.quantity}
                        onChange={(e) => {
                          const val = Math.max(1, parseInt(e.target.value) || 1);
                          const updated = [...orderLines];
                          updated[idx].quantity = val;
                          setOrderLines(updated);
                        }}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200 text-center font-mono focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    <div className="col-span-1 text-center">
                      {orderLines.length > 1 && (
                        <button
                          type="button"
                          onClick={() => setOrderLines(orderLines.filter((_, i) => i !== idx))}
                          className="text-slate-500 hover:text-rose-400 font-bold"
                        >
                          &times;
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setIsCreateOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/30 transition"
              >
                Create Draft Subscription
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
