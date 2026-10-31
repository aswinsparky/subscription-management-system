import React, { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Plan, PlanListResponse } from '../../types/plan';
import { 
  Calendar, 
  Search, 
  Plus, 
  Edit3, 
  Trash2, 
  X, 
  CheckCircle2, 
  AlertCircle, 
  ShieldCheck, 
  Clock, 
  ChevronLeft, 
  ChevronRight 
} from 'lucide-react';

export const PlanListPage: React.FC = () => {
  const { user } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [intervalFilter, setIntervalFilter] = useState<string>('ALL');

  // Modal states
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);

  // Form states
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    billing_interval: 'MONTHLY',
    plan_price: '999.00',
    minimum_quantity: 1,
    available_from: '',
    available_until: '',
    auto_close_enabled: false,
    early_cancellation_allowed: true,
    pause_allowed: true,
    renewal_allowed: true,
    status: 'ACTIVE',
  });

  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<PlanListResponse>('/plans/', {
        params: {
          query: searchQuery || undefined,
          billing_interval: intervalFilter !== 'ALL' ? intervalFilter : undefined,
          page,
          page_size: pageSize,
        },
      });
      setPlans(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, [page, intervalFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchPlans();
  };

  const openAddModal = () => {
    setEditingPlan(null);
    setFormData({
      name: '',
      description: '',
      billing_interval: 'MONTHLY',
      plan_price: '999.00',
      minimum_quantity: 1,
      available_from: '',
      available_until: '',
      auto_close_enabled: false,
      early_cancellation_allowed: true,
      pause_allowed: true,
      renewal_allowed: true,
      status: 'ACTIVE',
    });
    setFormError(null);
    setFormSuccess(null);
    setIsAddModalOpen(true);
  };

  const openEditModal = (plan: Plan) => {
    setEditingPlan(plan);
    setFormData({
      name: plan.name,
      description: plan.description || '',
      billing_interval: plan.billing_interval,
      plan_price: plan.plan_price,
      minimum_quantity: plan.minimum_quantity,
      available_from: plan.available_from ? plan.available_from.slice(0, 16) : '',
      available_until: plan.available_until ? plan.available_until.slice(0, 16) : '',
      auto_close_enabled: plan.auto_close_enabled,
      early_cancellation_allowed: plan.early_cancellation_allowed,
      pause_allowed: plan.pause_allowed,
      renewal_allowed: plan.renewal_allowed,
      status: plan.status,
    });
    setFormError(null);
    setFormSuccess(null);
  };

  const handleSavePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);

    try {
      const payload = {
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        billing_interval: formData.billing_interval,
        plan_price: formData.plan_price,
        minimum_quantity: Number(formData.minimum_quantity),
        available_from: formData.available_from ? new Date(formData.available_from).toISOString() : undefined,
        available_until: formData.available_until ? new Date(formData.available_until).toISOString() : undefined,
        auto_close_enabled: formData.auto_close_enabled,
        early_cancellation_allowed: formData.early_cancellation_allowed,
        pause_allowed: formData.pause_allowed,
        renewal_allowed: formData.renewal_allowed,
        status: formData.status,
      };

      if (editingPlan) {
        await apiClient.put(`/plans/${editingPlan.id}`, payload);
        setFormSuccess('Subscription plan updated.');
      } else {
        await apiClient.post('/plans/', payload);
        setFormSuccess('Subscription plan created.');
      }

      setTimeout(() => {
        setIsAddModalOpen(false);
        setEditingPlan(null);
        fetchPlans();
      }, 1200);
    } catch (err: any) {
      setFormError(err?.response?.data?.detail || 'Failed to save subscription plan.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeletePlan = async (plan: Plan) => {
    if (!window.confirm(`Delete or archive plan '${plan.name}'?`)) return;
    try {
      const res = await apiClient.delete<{ message: string }>(`/plans/${plan.id}`);
      alert(res.data.message);
      fetchPlans();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to delete plan.');
    }
  };

  const isAdmin = user?.role === 'ADMIN';

  return (
    <div className="space-y-6">
      {/* Header and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center space-x-2.5">
            <Calendar className="w-6 h-6 text-indigo-400" />
            <span>Subscription Plans</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Configure recurring intervals (Daily, Weekly, Monthly, Yearly), lifecycle policies, and minimum quantities
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={openAddModal}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>Create Plan</span>
          </button>
        )}
      </div>

      {/* Search and Interval Filter Bar */}
      <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-96">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search plans by name, code, description..."
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
          />
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
        </form>

        <div className="flex items-center space-x-2 w-full md:w-auto">
          <span className="text-xs font-medium text-slate-400 whitespace-nowrap">Interval:</span>
          <div className="flex items-center space-x-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
            {['ALL', 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY'].map((interval) => (
              <button
                key={interval}
                onClick={() => {
                  setIntervalFilter(interval);
                  setPage(1);
                }}
                className={`px-3 py-1 rounded-md text-[11px] font-semibold transition ${
                  intervalFilter === interval
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {interval}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Plans Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-3 text-center py-12 text-slate-500 text-xs font-mono">
            Loading subscription plans...
          </div>
        ) : plans.length === 0 ? (
          <div className="col-span-3 text-center py-12 text-slate-500 text-xs">
            No subscription plans found.
          </div>
        ) : (
          plans.map((p) => (
            <div
              key={p.id}
              className="bg-slate-950/80 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between hover:border-slate-700 transition shadow-xl space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                    {p.plan_code}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      p.status === 'ACTIVE'
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        : 'bg-rose-950 text-rose-300 border border-rose-800'
                    }`}
                  >
                    {p.status}
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-white">{p.name}</h3>
                  <p className="text-xs text-slate-400 mt-1 min-h-[32px] line-clamp-2">
                    {p.description || 'Standard recurring plan license.'}
                  </p>
                </div>

                <div className="flex items-baseline space-x-2 pt-2 border-t border-slate-800/80">
                  <span className="text-3xl font-extrabold text-white font-mono">₹{p.plan_price}</span>
                  <span className="text-xs text-indigo-400 font-semibold uppercase">
                    / {p.billing_interval.toLowerCase()}
                  </span>
                </div>

                <div className="text-[11px] text-slate-400 flex items-center space-x-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Min Quantity: <strong>{p.minimum_quantity} license(s)</strong></span>
                </div>

                {/* Lifecycle Policies Badges */}
                <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800/80 space-y-1.5 text-[11px]">
                  <span className="font-semibold text-slate-400 block mb-1">Lifecycle Policies:</span>
                  <div className="grid grid-cols-2 gap-1 text-slate-300">
                    <span className={p.early_cancellation_allowed ? 'text-emerald-400' : 'text-slate-500'}>
                      {p.early_cancellation_allowed ? '✓' : '✗'} Early Cancel
                    </span>
                    <span className={p.pause_allowed ? 'text-emerald-400' : 'text-slate-500'}>
                      {p.pause_allowed ? '✓' : '✗'} Pause Allowed
                    </span>
                    <span className={p.renewal_allowed ? 'text-emerald-400' : 'text-slate-500'}>
                      {p.renewal_allowed ? '✓' : '✗'} Auto-Renew
                    </span>
                    <span className={p.auto_close_enabled ? 'text-amber-400' : 'text-slate-500'}>
                      {p.auto_close_enabled ? '✓ Auto-Close' : '• Manual Close'}
                    </span>
                  </div>
                </div>

                {/* Availability period */}
                {(p.available_from || p.available_until) && (
                  <div className="text-[10px] text-slate-500 font-mono flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>
                      {p.available_from ? new Date(p.available_from).toLocaleDateString() : 'Immediate'} →{' '}
                      {p.available_until ? new Date(p.available_until).toLocaleDateString() : 'Indefinite'}
                    </span>
                  </div>
                )}
              </div>

              {isAdmin && (
                <div className="pt-3 border-t border-slate-800 flex items-center justify-end space-x-2">
                  <button
                    onClick={() => openEditModal(p)}
                    className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-amber-300 border border-slate-800 text-xs font-medium transition flex items-center space-x-1"
                  >
                    <Edit3 className="w-3 h-3" />
                    <span>Edit</span>
                  </button>
                  <button
                    onClick={() => handleDeletePlan(p)}
                    className="px-2.5 py-1 rounded bg-slate-900 hover:bg-rose-950 text-rose-400 border border-slate-800 text-xs font-medium transition flex items-center space-x-1"
                  >
                    <Trash2 className="w-3 h-3" />
                    <span>Delete/Archive</span>
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <span>Showing {plans.length} of {total} plans</span>
        <div className="flex items-center space-x-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 disabled:opacity-30 hover:bg-slate-800 transition"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="font-mono text-slate-300">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 disabled:opacity-30 hover:bg-slate-800 transition"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Plan Add / Edit Modal */}
      {(isAddModalOpen || editingPlan) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="relative w-full max-w-xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-4 text-slate-100">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-white text-base flex items-center space-x-2">
                <Calendar className="w-5 h-5 text-indigo-400" />
                <span>{editingPlan ? `Edit Plan: ${editingPlan.plan_code}` : 'Create Subscription Plan'}</span>
              </h3>
              <button
                onClick={() => {
                  setIsAddModalOpen(false);
                  setEditingPlan(null);
                }}
                className="p-1 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formSuccess && (
              <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>{formSuccess}</span>
              </div>
            )}

            {formError && (
              <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSavePlan} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-300 uppercase mb-1">Plan Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Starter Monthly"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-300 uppercase mb-1">Billing Interval *</label>
                  <select
                    value={formData.billing_interval}
                    onChange={(e) => setFormData({ ...formData, billing_interval: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="DAILY">DAILY</option>
                    <option value="WEEKLY">WEEKLY</option>
                    <option value="MONTHLY">MONTHLY</option>
                    <option value="YEARLY">YEARLY</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-300 uppercase mb-1">Plan Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={formData.plan_price}
                    onChange={(e) => setFormData({ ...formData, plan_price: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-300 uppercase mb-1">Minimum Quantity *</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={formData.minimum_quantity}
                    onChange={(e) => setFormData({ ...formData, minimum_quantity: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-300 uppercase mb-1">Available From</label>
                  <input
                    type="datetime-local"
                    value={formData.available_from}
                    onChange={(e) => setFormData({ ...formData, available_from: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-300 uppercase mb-1">Available Until</label>
                  <input
                    type="datetime-local"
                    value={formData.available_until}
                    onChange={(e) => setFormData({ ...formData, available_until: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">Description</label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Plan summary and terms..."
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* Lifecycle Policy Toggles */}
              <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                <span className="font-semibold text-slate-400 block uppercase tracking-wider text-[11px]">
                  Lifecycle Policies & Permissions:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-slate-300">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.early_cancellation_allowed}
                      onChange={(e) => setFormData({ ...formData, early_cancellation_allowed: e.target.checked })}
                      className="rounded bg-slate-900 border-slate-800 text-indigo-600 focus:ring-0"
                    />
                    <span>Allow Early Cancellation</span>
                  </label>

                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.pause_allowed}
                      onChange={(e) => setFormData({ ...formData, pause_allowed: e.target.checked })}
                      className="rounded bg-slate-900 border-slate-800 text-indigo-600 focus:ring-0"
                    />
                    <span>Allow Subscription Pause</span>
                  </label>

                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.renewal_allowed}
                      onChange={(e) => setFormData({ ...formData, renewal_allowed: e.target.checked })}
                      className="rounded bg-slate-900 border-slate-800 text-indigo-600 focus:ring-0"
                    />
                    <span>Allow Renewal</span>
                  </label>

                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.auto_close_enabled}
                      onChange={(e) => setFormData({ ...formData, auto_close_enabled: e.target.checked })}
                      className="rounded bg-slate-900 border-slate-800 text-indigo-600 focus:ring-0"
                    />
                    <span>Enable Auto-Close on Expiry</span>
                  </label>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsAddModalOpen(false);
                    setEditingPlan(null);
                  }}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
                >
                  {submitting ? 'Saving...' : editingPlan ? 'Update Plan' : 'Create Plan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
