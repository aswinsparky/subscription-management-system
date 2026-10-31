import React, { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Customer, CustomerListResponse, CustomerHistoryResponse } from '../../types/customer';
import { 
  Users, 
  Search, 
  Plus, 
  Edit3, 
  History, 
  X, 
  ChevronLeft, 
  ChevronRight, 
  CheckCircle2, 
  AlertCircle, 
  Building, 
  Phone, 
  Mail, 
  FileText,
  Clock
} from 'lucide-react';

export const CustomerListPage: React.FC = () => {
  const { user } = useAuth();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Modal states
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [historyCustomer, setHistoryCustomer] = useState<CustomerHistoryResponse | null>(null);

  // Form states
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    company_name: '',
    billing_address: '',
    tax_id: '',
    account_status: 'ACTIVE',
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<CustomerListResponse>('/customers/', {
        params: {
          query: searchQuery || undefined,
          account_status: statusFilter !== 'ALL' ? statusFilter : undefined,
          page,
          page_size: pageSize,
        },
      });
      setCustomers(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchCustomers();
  };

  const openAddModal = () => {
    setFormData({
      full_name: '',
      email: '',
      phone: '',
      company_name: '',
      billing_address: '100 Innovation Way, Suite 400',
      tax_id: '',
      account_status: 'ACTIVE',
    });
    setFormError(null);
    setFormSuccess(null);
    setIsAddModalOpen(true);
  };

  const openEditModal = (cust: Customer) => {
    setEditingCustomer(cust);
    setFormData({
      full_name: cust.full_name,
      email: cust.email,
      phone: cust.phone || '',
      company_name: cust.company_name || '',
      billing_address: cust.billing_address,
      tax_id: cust.tax_id || '',
      account_status: cust.account_status,
    });
    setFormError(null);
    setFormSuccess(null);
  };

  const openHistoryModal = async (cust: Customer) => {
    try {
      setHistoryCustomer(null);
      const res = await apiClient.get<CustomerHistoryResponse>(`/customers/${cust.id}/history`);
      setHistoryCustomer(res.data);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to fetch history');
    }
  };

  const handleCreateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await apiClient.post('/customers/', {
        full_name: formData.full_name.trim(),
        email: formData.email.trim().toLowerCase(),
        phone: formData.phone.trim() || undefined,
        company_name: formData.company_name.trim() || undefined,
        billing_address: formData.billing_address.trim(),
        tax_id: formData.tax_id.trim() || undefined,
        account_status: formData.account_status,
      });
      setFormSuccess('Customer created successfully.');
      setTimeout(() => {
        setIsAddModalOpen(false);
        fetchCustomers();
      }, 1200);
    } catch (err: any) {
      setFormError(err?.response?.data?.detail || 'Failed to create customer.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCustomer) return;
    setFormError(null);
    setSubmitting(true);
    try {
      await apiClient.put(`/customers/${editingCustomer.id}`, {
        full_name: formData.full_name.trim(),
        email: formData.email.trim().toLowerCase(),
        phone: formData.phone.trim() || undefined,
        company_name: formData.company_name.trim() || undefined,
        billing_address: formData.billing_address.trim(),
        tax_id: formData.tax_id.trim() || undefined,
        account_status: formData.account_status,
      });
      setFormSuccess('Customer profile updated.');
      setTimeout(() => {
        setEditingCustomer(null);
        fetchCustomers();
      }, 1200);
    } catch (err: any) {
      setFormError(err?.response?.data?.detail || 'Failed to update customer.');
    } finally {
      setSubmitting(false);
    }
  };

  const canManageCustomers = user?.role === 'ADMIN' || user?.role === 'STAFF';

  return (
    <div className="space-y-6">
      {/* Top Banner and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center space-x-2.5">
            <Users className="w-6 h-6 text-indigo-400" />
            <span>Customer Accounts</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Enterprise customer records, billing profiles, and historical subscriptions
          </p>
        </div>

        {canManageCustomers && (
          <button
            onClick={openAddModal}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>Add New Customer</span>
          </button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-96">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name, email, company, code..."
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
          />
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
        </form>

        <div className="flex items-center space-x-2 w-full md:w-auto">
          <span className="text-xs font-medium text-slate-400 whitespace-nowrap">Filter Status:</span>
          <div className="flex items-center space-x-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
            {['ALL', 'ACTIVE', 'SUSPENDED', 'ARCHIVED'].map((st) => (
              <button
                key={st}
                onClick={() => {
                  setStatusFilter(st);
                  setPage(1);
                }}
                className={`px-3 py-1 rounded-md text-[11px] font-semibold transition ${
                  statusFilter === st
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Customers Data Table */}
      <div className="bg-slate-950/80 rounded-xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Code</th>
                <th className="py-3 px-4">Customer & Company</th>
                <th className="py-3 px-4">Contact</th>
                <th className="py-3 px-4">Tax ID</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Joined</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    Loading customer records...
                  </td>
                </tr>
              ) : customers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No customers found matching the search criteria.
                  </td>
                </tr>
              ) : (
                customers.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-900/40 transition">
                    <td className="py-3 px-4 font-bold text-indigo-400">{c.customer_code}</td>
                    <td className="py-3 px-4 font-sans">
                      <div className="font-semibold text-white">{c.full_name}</div>
                      {c.company_name && (
                        <div className="text-[11px] text-slate-400 flex items-center space-x-1 mt-0.5">
                          <Building className="w-3 h-3 text-slate-500" />
                          <span>{c.company_name}</span>
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4 font-sans text-slate-300">
                      <div className="flex items-center space-x-1">
                        <Mail className="w-3 h-3 text-slate-500" />
                        <span>{c.email}</span>
                      </div>
                      {c.phone && (
                        <div className="flex items-center space-x-1 text-slate-500 text-[11px] mt-0.5">
                          <Phone className="w-3 h-3" />
                          <span>{c.phone}</span>
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                      {c.tax_id || '—'}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          c.account_status === 'ACTIVE'
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : c.account_status === 'SUSPENDED'
                            ? 'bg-amber-950 text-amber-300 border border-amber-800'
                            : 'bg-slate-800 text-slate-400 border border-slate-700'
                        }`}
                      >
                        {c.account_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-500 text-[11px]">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right space-x-2 font-sans">
                      <button
                        onClick={() => openHistoryModal(c)}
                        title="View Subscription & Quotation History"
                        className="px-2 py-1 rounded bg-slate-900 hover:bg-slate-800 text-indigo-300 border border-slate-800 text-[11px] font-medium transition inline-flex items-center space-x-1"
                      >
                        <History className="w-3 h-3" />
                        <span>History</span>
                      </button>
                      {canManageCustomers && (
                        <button
                          onClick={() => openEditModal(c)}
                          title="Edit Customer"
                          className="px-2 py-1 rounded bg-slate-900 hover:bg-slate-800 text-amber-300 border border-slate-800 text-[11px] font-medium transition inline-flex items-center space-x-1"
                        >
                          <Edit3 className="w-3 h-3" />
                          <span>Edit</span>
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>
            Showing {customers.length} of {total} customer records
          </span>
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
      </div>

      {/* Add / Edit Customer Modal */}
      {(isAddModalOpen || editingCustomer) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="relative w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-4 text-slate-100">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-white text-base flex items-center space-x-2">
                <Users className="w-5 h-5 text-indigo-400" />
                <span>{editingCustomer ? `Edit Customer: ${editingCustomer.customer_code}` : 'Add New Customer Profile'}</span>
              </h3>
              <button
                onClick={() => {
                  setIsAddModalOpen(false);
                  setEditingCustomer(null);
                }}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
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

            <form onSubmit={editingCustomer ? handleUpdateCustomer : handleCreateCustomer} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Full Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Email *</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Company Name</label>
                  <input
                    type="text"
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Phone</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Tax ID / VAT</label>
                  <input
                    type="text"
                    value={formData.tax_id}
                    onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })}
                    placeholder="e.g. GSTIN / EIN"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Account Status</label>
                  <select
                    value={formData.account_status}
                    onChange={(e) => setFormData({ ...formData, account_status: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                  >
                    <option value="ACTIVE">ACTIVE</option>
                    <option value="SUSPENDED">SUSPENDED</option>
                    <option value="ARCHIVED">ARCHIVED</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Billing Address *</label>
                <textarea
                  rows={2}
                  required
                  value={formData.billing_address}
                  onChange={(e) => setFormData({ ...formData, billing_address: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsAddModalOpen(false);
                    setEditingCustomer(null);
                  }}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
                >
                  <span>{submitting ? 'Saving...' : editingCustomer ? 'Update Customer' : 'Create Customer'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Customer History & Profile Modal */}
      {historyCustomer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-6 text-slate-100">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="font-bold text-white text-base flex items-center space-x-2">
                  <FileText className="w-5 h-5 text-indigo-400" />
                  <span>Customer Record & Lifecycle History</span>
                </h3>
                <p className="text-xs text-slate-400">
                  {historyCustomer.customer.full_name} ({historyCustomer.customer.customer_code})
                </p>
              </div>
              <button
                onClick={() => setHistoryCustomer(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Profile Summary Card */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Email</span>
                <span className="text-slate-200">{historyCustomer.customer.email}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Phone</span>
                <span className="text-slate-200">{historyCustomer.customer.phone || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Company</span>
                <span className="text-slate-200">{historyCustomer.customer.company_name || 'Individual'}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Tax ID</span>
                <span className="text-slate-200">{historyCustomer.customer.tax_id || 'N/A'}</span>
              </div>
              <div className="col-span-2 sm:col-span-4 font-sans text-slate-400 pt-2 border-t border-slate-900">
                <span className="font-semibold text-slate-300">Billing Address: </span>
                {historyCustomer.customer.billing_address}
              </div>
            </div>

            {/* Subscriptions History Section */}
            <div className="space-y-3">
              <h4 className="font-bold text-sm text-white flex items-center space-x-2">
                <Clock className="w-4 h-4 text-emerald-400" />
                <span>Associated Subscriptions ({historyCustomer.subscriptions.length})</span>
              </h4>

              {historyCustomer.subscriptions.length === 0 ? (
                <p className="text-xs text-slate-500 italic bg-slate-950 p-4 rounded-lg border border-slate-800">
                  No subscriptions established for this customer yet.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono border border-slate-800 rounded-lg overflow-hidden">
                    <thead className="bg-slate-950 text-slate-400">
                      <tr>
                        <th className="p-2">Number</th>
                        <th className="p-2">Interval</th>
                        <th className="p-2">Total Amount</th>
                        <th className="p-2">Status</th>
                        <th className="p-2">Next Billing</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                      {historyCustomer.subscriptions.map((s) => (
                        <tr key={s.id}>
                          <td className="p-2 font-bold text-indigo-400">{s.subscription_number}</td>
                          <td className="p-2 text-slate-300">{s.billing_interval}</td>
                          <td className="p-2 font-semibold text-white">₹{s.total_amount}</td>
                          <td className="p-2">
                            <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800">
                              {s.status}
                            </span>
                          </td>
                          <td className="p-2 text-slate-400">{new Date(s.next_billing_date).toLocaleDateString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Quotations History Section */}
            <div className="space-y-3">
              <h4 className="font-bold text-sm text-white flex items-center space-x-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <span>Associated Quotations ({historyCustomer.quotations.length})</span>
              </h4>

              {historyCustomer.quotations.length === 0 ? (
                <p className="text-xs text-slate-500 italic bg-slate-950 p-4 rounded-lg border border-slate-800">
                  No quotations on record for this customer.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono border border-slate-800 rounded-lg overflow-hidden">
                    <thead className="bg-slate-950 text-slate-400">
                      <tr>
                        <th className="p-2">Quotation #</th>
                        <th className="p-2">Quote Date</th>
                        <th className="p-2">Total Amount</th>
                        <th className="p-2">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                      {historyCustomer.quotations.map((q) => (
                        <tr key={q.id}>
                          <td className="p-2 font-bold text-indigo-400">{q.quotation_number}</td>
                          <td className="p-2 text-slate-400">{new Date(q.quotation_date).toLocaleDateString()}</td>
                          <td className="p-2 font-semibold text-white">₹{q.total}</td>
                          <td className="p-2">
                            <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
                              {q.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
