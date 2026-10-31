import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { CustomerPortalOverview } from '../../types/portal';
import { 
  Repeat, 
  FileCheck2, 
  Pause, 
  Play, 
  XCircle, 
  CheckCircle, 
  Edit3, 
  ShieldCheck, 
  AlertCircle
} from 'lucide-react';

export const CustomerPortalPage: React.FC = () => {
  const [data, setData] = useState<CustomerPortalOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Edit Profile Modal
  const [isEditProfileOpen, setIsEditProfileOpen] = useState<boolean>(false);
  const [phone, setPhone] = useState<string>('');
  const [companyName, setCompanyName] = useState<string>('');
  const [billingAddress, setBillingAddress] = useState<string>('');
  const [editLoading, setEditLoading] = useState<boolean>(false);

  const fetchOverview = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<CustomerPortalOverview>('/portal/overview');
      setData(res.data);
      if (res.data?.profile) {
        setPhone(res.data.profile.phone || '');
        setCompanyName(res.data.profile.company_name || '');
        setBillingAddress(res.data.profile.billing_address || '');
      }
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load customer portal.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setEditLoading(true);
      await apiClient.put('/portal/profile', {
        phone: phone || null,
        company_name: companyName || null,
        billing_address: billingAddress,
      });
      setIsEditProfileOpen(false);
      await fetchOverview();
      alert('Profile updated successfully!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setEditLoading(false);
    }
  };

  const handlePauseSub = async (subId: number) => {
    const reason = prompt('Please enter a reason for pausing your subscription:');
    if (reason === null) return;
    try {
      await apiClient.post(`/portal/subscriptions/${subId}/pause`, { reason });
      await fetchOverview();
      alert('Subscription paused successfully.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to pause subscription.');
    }
  };

  const handleResumeSub = async (subId: number) => {
    try {
      await apiClient.post(`/portal/subscriptions/${subId}/resume`, {});
      await fetchOverview();
      alert('Subscription resumed back to active status!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to resume subscription.');
    }
  };

  const handleCancelSub = async (subId: number) => {
    const reason = prompt('Please enter a cancellation reason:');
    if (reason === null) return;
    if (!confirm('Are you sure you want to cancel this subscription?')) return;
    try {
      await apiClient.post(`/portal/subscriptions/${subId}/cancel`, { reason });
      await fetchOverview();
      alert('Subscription cancelled.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to cancel subscription.');
    }
  };

  const handleAcceptQuote = async (quoteId: number) => {
    if (!confirm('Accept this quotation and convert it into an active subscription?')) return;
    try {
      await apiClient.post(`/portal/quotations/${quoteId}/accept`);
      await fetchOverview();
      alert('Quotation accepted! New subscription created successfully.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to accept quotation.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-950/60 p-6 rounded-2xl border border-slate-800">
        <div>
          <div className="flex items-center space-x-2.5 text-indigo-400 mb-1">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-bold text-white tracking-wide">
              Customer Self-Service Portal
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            Tenant-isolated self-service management: review active subscriptions, manage contracts, and accept proposals.
          </p>
        </div>

        <button
          onClick={() => setIsEditProfileOpen(true)}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition self-start md:self-auto"
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>Edit Account Profile</span>
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 text-xs">Loading customer portal...</div>
      ) : error ? (
        <div className="p-6 bg-slate-950/60 rounded-2xl border border-slate-800 text-rose-400 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      ) : !data ? (
        <div className="p-12 text-center text-slate-500 text-xs">No account data found.</div>
      ) : (
        <>
          {/* Profile Overview Card & Quick Stats */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 p-5 bg-slate-950/60 rounded-2xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-indigo-950 border border-indigo-800 flex items-center justify-center font-bold text-indigo-300 text-sm">
                    {data.profile.full_name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-base leading-tight">
                      {data.profile.full_name}
                    </h3>
                    <p className="text-xs text-slate-400 font-mono">
                      {data.profile.customer_code} &bull; {data.profile.email}
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800">
                  {data.profile.account_status}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-slate-500 block mb-0.5">Company</span>
                  <span className="text-slate-200 font-medium">
                    {data.profile.company_name || 'Individual Account'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block mb-0.5">Phone Number</span>
                  <span className="text-slate-200 font-mono">
                    {data.profile.phone || 'Not provided'}
                  </span>
                </div>
                <div className="sm:col-span-2">
                  <span className="text-slate-500 block mb-0.5">Billing Address</span>
                  <span className="text-slate-300 leading-relaxed font-sans">
                    {data.profile.billing_address}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Financial Summary */}
            <div className="p-5 bg-slate-950/60 rounded-2xl border border-slate-800 flex flex-col justify-between">
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Active Recurring Subscriptions
                </span>
                <div className="text-3xl font-extrabold text-white font-mono mt-2">
                  ${Number(data.total_active_mrr).toFixed(2)}
                  <span className="text-xs text-slate-500 font-normal ml-1">/ month</span>
                </div>
              </div>
              <div className="pt-4 border-t border-slate-800/80 text-xs text-slate-400 flex justify-between">
                <span>Active Contracts: {data.active_subscriptions.filter((s) => s.status === 'ACTIVE').length}</span>
                <span>Pending Quotes: {data.pending_quotations.length}</span>
              </div>
            </div>
          </div>

          {/* Pending Quotations Section */}
          {data.pending_quotations.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center space-x-2 text-indigo-400">
                <FileCheck2 className="w-4 h-4" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-white">
                  Pending Quotations ({data.pending_quotations.length})
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.pending_quotations.map((quote) => (
                  <div
                    key={quote.id}
                    className="p-4 bg-slate-950/60 rounded-2xl border border-indigo-900/40 shadow-lg space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-indigo-300 text-xs">
                        {quote.quotation_number}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                        {quote.status}
                      </span>
                    </div>

                    <div className="flex justify-between items-baseline">
                      <div>
                        <div className="text-xs font-semibold text-slate-200">
                          {quote.plan_name || `Plan #${quote.plan_id}`}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono">
                          Expires: {new Date(quote.expiration_date).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="font-mono font-bold text-white text-base">
                          ${Number(quote.total).toFixed(2)}
                        </span>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-800/80 flex justify-end">
                      <button
                        onClick={() => handleAcceptQuote(quote.id)}
                        className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition flex items-center space-x-1 shadow-md shadow-emerald-600/20"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span>Accept Proposal</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Active Subscriptions Section */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-indigo-400">
              <Repeat className="w-4 h-4" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-white">
                My Subscriptions ({data.active_subscriptions.length})
              </h3>
            </div>

            <div className="bg-slate-950/60 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
              {data.active_subscriptions.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-xs">
                  No subscriptions found in your account.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
                      <tr>
                        <th className="py-3 px-4">Subscription</th>
                        <th className="py-3 px-4">Plan</th>
                        <th className="py-3 px-4">Interval</th>
                        <th className="py-3 px-4">Next Renewal</th>
                        <th className="py-3 px-4 text-right">Amount</th>
                        <th className="py-3 px-4 text-center">Status</th>
                        <th className="py-3 px-4 text-right">Self-Service Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-sans">
                      {data.active_subscriptions.map((sub) => (
                        <tr key={sub.id} className="hover:bg-slate-900/40 transition">
                          <td className="py-3 px-4 font-mono font-semibold text-indigo-300">
                            {sub.subscription_number}
                          </td>
                          <td className="py-3 px-4 text-slate-200 font-medium">
                            {sub.plan?.name || `Plan #${sub.plan_id}`}
                          </td>
                          <td className="py-3 px-4 font-mono text-slate-400">
                            {sub.billing_interval}
                          </td>
                          <td className="py-3 px-4 font-mono text-slate-300 text-[11px]">
                            {new Date(sub.next_billing_date).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4 text-right font-mono font-bold text-white">
                            ${Number(sub.total_amount).toFixed(2)}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span
                              className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                                sub.status === 'ACTIVE'
                                  ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                                  : sub.status === 'PAUSED'
                                  ? 'bg-amber-950 text-amber-300 border-amber-800'
                                  : 'bg-slate-800 text-slate-400 border-slate-700'
                              }`}
                            >
                              {sub.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <div className="inline-flex items-center space-x-1.5">
                              {sub.status === 'ACTIVE' && (
                                <button
                                  onClick={() => handlePauseSub(sub.id)}
                                  className="px-2.5 py-1 rounded bg-amber-900/60 hover:bg-amber-800 text-amber-200 border border-amber-700 transition flex items-center space-x-1 text-[11px]"
                                  title="Pause Subscription"
                                >
                                  <Pause className="w-3 h-3" />
                                  <span>Pause</span>
                                </button>
                              )}

                              {sub.status === 'PAUSED' && (
                                <button
                                  onClick={() => handleResumeSub(sub.id)}
                                  className="px-2.5 py-1 rounded bg-emerald-900/60 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 transition flex items-center space-x-1 text-[11px]"
                                  title="Resume Subscription"
                                >
                                  <Play className="w-3 h-3" />
                                  <span>Resume</span>
                                </button>
                              )}

                              {(sub.status === 'ACTIVE' || sub.status === 'PAUSED') && (
                                <button
                                  onClick={() => handleCancelSub(sub.id)}
                                  className="px-2.5 py-1 rounded bg-rose-950 hover:bg-rose-900 text-rose-300 border border-rose-800 transition flex items-center space-x-1 text-[11px]"
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
          </div>

          {/* Edit Profile Modal */}
          {isEditProfileOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
              <form
                onSubmit={handleUpdateProfile}
                className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl"
              >
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <Edit3 className="w-4 h-4 text-indigo-400" />
                    <span>Update Account Details</span>
                  </h3>
                  <button
                    type="button"
                    onClick={() => setIsEditProfileOpen(false)}
                    className="text-slate-400 hover:text-white text-lg font-bold"
                  >
                    &times;
                  </button>
                </div>

                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block text-slate-400 mb-1">Company Name</label>
                    <input
                      type="text"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      placeholder="Organization or Company Name"
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1">Contact Phone</label>
                    <input
                      type="text"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+1-555-0100"
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1">Billing Address</label>
                    <textarea
                      value={billingAddress}
                      onChange={(e) => setBillingAddress(e.target.value)}
                      rows={3}
                      required
                      placeholder="Street, City, State, Postal Code, Country"
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsEditProfileOpen(false)}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={editLoading}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition disabled:opacity-50"
                  >
                    {editLoading ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </>
      )}
    </div>
  );
};
