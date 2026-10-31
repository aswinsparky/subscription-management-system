import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { 
  Download, 
  CheckCircle, 
  XCircle, 
  Plus, 
  Search, 
  Filter, 
  RefreshCw
} from 'lucide-react';

interface InvoiceItem {
  id: number;
  item_description: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  total_amount: number;
}

interface Invoice {
  id: number;
  invoice_number: string;
  customer_id: number;
  invoice_date: string;
  due_date: string;
  status: string;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  total_amount: number;
  amount_paid: number;
  amount_due: number;
  payment_terms: string;
  notes: string | null;
  items: InvoiceItem[];
}

interface InvoiceListResponse {
  items: Invoice[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export function InvoicesPage() {
  const { user } = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);

  // Manual Creation Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [customerId, setCustomerId] = useState('');
  const [description, setDescription] = useState('');
  const [unitPrice, setUnitPrice] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [paymentTerms, setPaymentTerms] = useState('Immediate');

  const fetchInvoices = async () => {
    try {
      setLoading(true);
      let url = `/invoices?page=${page}&page_size=15`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;

      const res = await apiClient.get<InvoiceListResponse>(url);
      setInvoices(res.data.items);
    } catch (err) {
      console.error('Failed to load invoices', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, [page, statusFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchInvoices();
  };

  const handleDownloadPDF = async (invoiceId: number, invoiceNumber: string) => {
    try {
      const response = await apiClient.get(`/invoices/${invoiceId}/pdf`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${invoiceNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch {
      alert('Failed to download invoice PDF.');
    }
  };

  const handleConfirm = async (id: number) => {
    try {
      await apiClient.post(`/invoices/${id}/confirm`);
      fetchInvoices();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to confirm invoice');
    }
  };

  const handleCancel = async (id: number) => {
    if (!confirm('Are you sure you want to cancel this invoice?')) return;
    try {
      await apiClient.post(`/invoices/${id}/cancel`);
      fetchInvoices();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to cancel invoice');
    }
  };

  const handleCreateInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/invoices', {
        customer_id: parseInt(customerId),
        payment_terms: paymentTerms,
        items: [
          {
            item_description: description,
            quantity: parseInt(quantity),
            unit_price: parseFloat(unitPrice),
            tax_rate_snapshot: 0,
          }
        ]
      });
      setIsCreateOpen(false);
      setDescription('');
      setUnitPrice('');
      fetchInvoices();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to create invoice');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PAID':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">PAID</span>;
      case 'PARTIALLY_PAID':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">PARTIAL</span>;
      case 'OVERDUE':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 animate-pulse">OVERDUE</span>;
      case 'CONFIRMED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">CONFIRMED</span>;
      case 'CANCELLED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">CANCELLED</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-600/20 text-slate-300 border border-slate-600/30">DRAFT</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950/70 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <h2 className="text-xl font-extrabold text-white">Invoice Management</h2>
          <p className="text-slate-400 text-xs mt-0.5">
            View, generate, confirm, cancel, and download official PDF invoices.
          </p>
        </div>
        {user?.role !== 'CUSTOMER' && (
          <button
            onClick={() => setIsCreateOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition"
          >
            <Plus className="w-4 h-4" />
            <span>Create Invoice</span>
          </button>
        )}
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-3 bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
        <form onSubmit={handleSearch} className="flex-1 flex items-center space-x-2 w-full md:w-auto">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search invoice number or notes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
            />
          </div>
          <button
            type="submit"
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
          >
            Search
          </button>
        </form>

        <div className="flex items-center space-x-2 w-full md:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="PARTIALLY_PAID">Partially Paid</option>
            <option value="PAID">Paid</option>
            <option value="OVERDUE">Overdue</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
          <button
            onClick={fetchInvoices}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition"
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Invoice Table */}
      <div className="bg-slate-950/60 rounded-2xl border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-5 py-3.5">Invoice #</th>
                <th className="px-5 py-3.5">Invoice Date</th>
                <th className="px-5 py-3.5">Due Date</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5 text-right">Total ($)</th>
                <th className="px-5 py-3.5 text-right">Paid ($)</th>
                <th className="px-5 py-3.5 text-right">Balance Due ($)</th>
                <th className="px-5 py-3.5 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {invoices.length > 0 ? (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-900/50 transition">
                    <td className="px-5 py-3.5 font-mono font-bold text-indigo-400">
                      {inv.invoice_number}
                    </td>
                    <td className="px-5 py-3.5 text-slate-400">
                      {new Date(inv.invoice_date).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3.5 text-slate-400">
                      {new Date(inv.due_date).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3.5">
                      {getStatusBadge(inv.status)}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono font-semibold text-white">
                      ${Number(inv.total_amount).toFixed(2)}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono text-emerald-400 font-semibold">
                      ${Number(inv.amount_paid).toFixed(2)}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono font-bold text-rose-400">
                      ${Number(inv.amount_due).toFixed(2)}
                    </td>
                    <td className="px-5 py-3.5 text-center">
                      <div className="flex items-center justify-center space-x-1.5">
                        <button
                          onClick={() => handleDownloadPDF(inv.id, inv.invoice_number)}
                          className="p-1.5 bg-slate-800 hover:bg-indigo-600/30 text-indigo-400 hover:text-indigo-300 rounded-lg transition border border-slate-700/60"
                          title="Download PDF"
                        >
                          <Download className="w-3.5 h-3.5" />
                        </button>

                        {inv.status === 'DRAFT' && user?.role !== 'CUSTOMER' && (
                          <button
                            onClick={() => handleConfirm(inv.id)}
                            className="p-1.5 bg-slate-800 hover:bg-emerald-600/30 text-emerald-400 hover:text-emerald-300 rounded-lg transition border border-slate-700/60"
                            title="Confirm Invoice"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                          </button>
                        )}

                        {inv.status !== 'PAID' && inv.status !== 'CANCELLED' && user?.role !== 'CUSTOMER' && (
                          <button
                            onClick={() => handleCancel(inv.id)}
                            className="p-1.5 bg-slate-800 hover:bg-rose-600/30 text-rose-400 hover:text-rose-300 rounded-lg transition border border-slate-700/60"
                            title="Cancel Invoice"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-5 py-8 text-center text-slate-500">
                    {loading ? 'Loading invoices...' : 'No invoices found.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manual Create Invoice Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">Create New Invoice</h3>
            <form onSubmit={handleCreateInvoice} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Customer ID</label>
                <input
                  type="number"
                  required
                  placeholder="e.g. 1"
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Item Description</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Professional Cloud Services"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Quantity</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Unit Price ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    placeholder="199.00"
                    value={unitPrice}
                    onChange={(e) => setUnitPrice(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                  />
                </div>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Payment Terms</label>
                <select
                  value={paymentTerms}
                  onChange={(e) => setPaymentTerms(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                >
                  <option value="Immediate">Immediate</option>
                  <option value="Net 15">Net 15 Days</option>
                  <option value="Net 30">Net 30 Days</option>
                </select>
              </div>
              <div className="flex items-center justify-end space-x-2 pt-3">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition"
                >
                  Create Invoice
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
