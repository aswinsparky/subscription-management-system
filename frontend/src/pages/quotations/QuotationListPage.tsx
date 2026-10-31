import React, { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Quotation, QuotationListResponse } from '../../types/quotation';
import { Customer } from '../../types/customer';
import { Product } from '../../types/product';
import { Plan } from '../../types/plan';
import { 
  FileCheck2, 
  Search, 
  Plus, 
  ArrowRightCircle, 
  CheckCircle2, 
  AlertCircle, 
  X, 
  ChevronLeft, 
  ChevronRight
} from 'lucide-react';

export const QuotationListPage: React.FC = () => {
  const { user } = useAuth();
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Related data for creating quotes
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [selectedQuote, setSelectedQuote] = useState<Quotation | null>(null);

  // Form states
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | ''>('');
  const [selectedPlanId, setSelectedPlanId] = useState<number | ''>('');
  const [expirationDays, setExpirationDays] = useState<number>(30);
  const [quoteItems, setQuoteItems] = useState<Array<{ product_id: number; variant_id: number | null; quantity: number; unit_price: string }>>([]);

  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const fetchQuotations = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<QuotationListResponse>('/quotations/', {
        params: {
          query: searchQuery || undefined,
          status: statusFilter !== 'ALL' ? statusFilter : undefined,
          page,
          page_size: pageSize,
        },
      });
      setQuotations(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  const loadReferenceData = async () => {
    try {
      const [custRes, prodRes, planRes] = await Promise.all([
        apiClient.get('/customers/?page_size=100'),
        apiClient.get('/products/?page_size=100'),
        apiClient.get('/plans/?page_size=100'),
      ]);
      setCustomers(custRes.data.items || []);
      setProducts(prodRes.data.items || []);
      setPlans(planRes.data.items || []);
    } catch {
      // Catch silently
    }
  };

  useEffect(() => {
    fetchQuotations();
  }, [page, statusFilter]);

  useEffect(() => {
    if (user?.role === 'ADMIN' || user?.role === 'STAFF') {
      loadReferenceData();
    }
  }, [user]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchQuotations();
  };

  const openCreateModal = () => {
    setSelectedCustomerId(customers[0]?.id || '');
    setSelectedPlanId(plans[0]?.id || '');
    setExpirationDays(30);

    if (products[0]) {
      setQuoteItems([
        {
          product_id: products[0].id,
          variant_id: products[0].variants[0]?.id || null,
          quantity: 1,
          unit_price: products[0].variants[0]?.final_price || products[0].sales_price,
        },
      ]);
    } else {
      setQuoteItems([]);
    }

    setFormError(null);
    setFormSuccess(null);
    setIsCreateOpen(true);
  };

  const addLineItem = () => {
    if (!products[0]) return;
    const prod = products[0];
    const initialPrice = prod.variants[0]?.final_price || prod.sales_price;
    setQuoteItems([
      ...quoteItems,
      {
        product_id: prod.id,
        variant_id: prod.variants[0]?.id || null,
        quantity: 1,
        unit_price: initialPrice,
      },
    ]);
  };

  const removeLineItem = (idx: number) => {
    const updated = [...quoteItems];
    updated.splice(idx, 1);
    setQuoteItems(updated);
  };

  const updateLineProduct = (idx: number, productId: number) => {
    const prod = products.find((p) => p.id === productId);
    if (!prod) return;
    const updated = [...quoteItems];
    const variantId = prod.variants[0]?.id || null;
    const price = prod.variants[0]?.final_price || prod.sales_price;
    updated[idx] = {
      product_id: prod.id,
      variant_id: variantId,
      quantity: updated[idx].quantity,
      unit_price: price,
    };
    setQuoteItems(updated);
  };

  const updateLineVariant = (idx: number, variantIdStr: string) => {
    const updated = [...quoteItems];
    const line = updated[idx];
    const prod = products.find((p) => p.id === line.product_id);
    if (!prod) return;

    if (!variantIdStr) {
      line.variant_id = null;
      line.unit_price = prod.sales_price;
    } else {
      const vId = Number(variantIdStr);
      const variant = prod.variants.find((v) => v.id === vId);
      line.variant_id = vId;
      line.unit_price = variant ? variant.final_price : prod.sales_price;
    }
    setQuoteItems(updated);
  };

  const updateLineQuantity = (idx: number, qty: number) => {
    const updated = [...quoteItems];
    updated[idx].quantity = Math.max(1, qty);
    setQuoteItems(updated);
  };

  const calculatedSubtotal = quoteItems.reduce((acc, item) => {
    const price = parseFloat(item.unit_price) || 0;
    return acc + price * item.quantity;
  }, 0);

  const handleCreateQuotation = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!selectedCustomerId || !selectedPlanId) {
      setFormError('Please select both a Customer and a Plan.');
      return;
    }
    if (quoteItems.length === 0) {
      setFormError('Please add at least one product line item.');
      return;
    }

    setSubmitting(true);
    try {
      const expDate = new Date();
      expDate.setDate(expDate.getDate() + expirationDays);

      const payload = {
        customer_id: Number(selectedCustomerId),
        plan_id: Number(selectedPlanId),
        expiration_date: expDate.toISOString(),
        items: quoteItems.map((item) => ({
          product_id: item.product_id,
          variant_id: item.variant_id || undefined,
          quantity: item.quantity,
          unit_price: item.unit_price,
        })),
      };

      await apiClient.post('/quotations/', payload);
      setFormSuccess('Quotation created successfully.');
      setTimeout(() => {
        setIsCreateOpen(false);
        fetchQuotations();
      }, 1200);
    } catch (err: any) {
      setFormError(err?.response?.data?.detail || 'Failed to create quotation.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleConvertToSubscription = async (quote: Quotation) => {
    if (!window.confirm(`Convert accepted quotation ${quote.quotation_number} into a live Subscription?`)) {
      return;
    }

    try {
      const res = await apiClient.post<{ message: string; subscription_number: string }>(
        `/quotations/${quote.id}/convert`
      );
      alert(`Success! Created Subscription: ${res.data.subscription_number}`);
      fetchQuotations();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Conversion failed.');
    }
  };

  const canManageQuotations = user?.role === 'ADMIN' || user?.role === 'STAFF';

  return (
    <div className="space-y-6">
      {/* Header and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center space-x-2.5">
            <FileCheck2 className="w-6 h-6 text-indigo-400" />
            <span>Quotations & Conversion Pipeline</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Build proposals, enforce plan minimums, and seamlessly convert accepted quotes into recurring subscriptions
          </p>
        </div>

        {canManageQuotations && (
          <button
            onClick={openCreateModal}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>Create Quotation</span>
          </button>
        )}
      </div>

      {/* Search & Status Filters */}
      <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-96">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search quotation #, customer name, code..."
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
          />
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
        </form>

        <div className="flex items-center space-x-2 w-full md:w-auto">
          <span className="text-xs font-medium text-slate-400 whitespace-nowrap">Status:</span>
          <div className="flex items-center space-x-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs overflow-x-auto">
            {['ALL', 'DRAFT', 'SENT', 'ACCEPTED', 'EXPIRED', 'REJECTED'].map((st) => (
              <button
                key={st}
                onClick={() => {
                  setStatusFilter(st);
                  setPage(1);
                }}
                className={`px-3 py-1 rounded-md text-[11px] font-semibold transition whitespace-nowrap ${
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

      {/* Quotations Table */}
      <div className="bg-slate-950/80 rounded-xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Quotation #</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4">Plan</th>
                <th className="py-3 px-4">Quote Date</th>
                <th className="py-3 px-4">Expires</th>
                <th className="py-3 px-4">Total Amount</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500 font-sans">
                    Loading quotation records...
                  </td>
                </tr>
              ) : quotations.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500 font-sans">
                    No quotation records found.
                  </td>
                </tr>
              ) : (
                quotations.map((q) => (
                  <tr key={q.id} className="hover:bg-slate-900/40 transition">
                    <td className="py-3 px-4 font-bold text-indigo-400">{q.quotation_number}</td>
                    <td className="py-3 px-4 font-sans">
                      <div className="font-semibold text-white">{q.customer_name || 'Customer'}</div>
                      <span className="text-[10px] text-slate-400 font-mono">{q.customer_code}</span>
                    </td>
                    <td className="py-3 px-4 font-sans text-slate-300">{q.plan_name || 'Custom Plan'}</td>
                    <td className="py-3 px-4 text-slate-400">{new Date(q.quotation_date).toLocaleDateString()}</td>
                    <td className="py-3 px-4 text-slate-400">{new Date(q.expiration_date).toLocaleDateString()}</td>
                    <td className="py-3 px-4 font-bold text-emerald-400 text-sm">₹{q.total}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          q.status === 'ACCEPTED'
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : q.status === 'SENT'
                            ? 'bg-indigo-950 text-indigo-300 border border-indigo-800'
                            : q.status === 'EXPIRED'
                            ? 'bg-rose-950 text-rose-300 border border-rose-800'
                            : 'bg-slate-900 text-slate-400 border border-slate-700'
                        }`}
                      >
                        {q.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right space-x-2 font-sans">
                      <button
                        onClick={() => setSelectedQuote(q)}
                        className="px-2 py-1 rounded bg-slate-900 hover:bg-slate-800 text-indigo-300 border border-slate-800 text-[11px] font-medium transition"
                      >
                        View Lines
                      </button>

                      {canManageQuotations && !q.converted_to_subscription_id && q.status !== 'EXPIRED' && (
                        <button
                          onClick={() => handleConvertToSubscription(q)}
                          className="px-2.5 py-1 rounded bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-800 text-[11px] font-semibold transition inline-flex items-center space-x-1"
                        >
                          <ArrowRightCircle className="w-3.5 h-3.5" />
                          <span>Convert to Sub</span>
                        </button>
                      )}

                      {q.converted_to_subscription_id && (
                        <span className="text-[10px] text-emerald-400 font-mono font-semibold">
                          Converted ✓
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>Showing {quotations.length} of {total} quotations</span>
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

      {/* Create Quotation Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-4 text-slate-100">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-white text-base flex items-center space-x-2">
                <FileCheck2 className="w-5 h-5 text-indigo-400" />
                <span>Create New Quotation</span>
              </h3>
              <button onClick={() => setIsCreateOpen(false)} className="p-1 text-slate-400 hover:text-white">
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

            <form onSubmit={handleCreateQuotation} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-300 uppercase mb-1">Select Customer *</label>
                  <select
                    value={selectedCustomerId}
                    onChange={(e) => setSelectedCustomerId(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500 font-sans"
                  >
                    {customers.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.full_name} ({c.customer_code})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-300 uppercase mb-1">Target Subscription Plan *</label>
                  <select
                    value={selectedPlanId}
                    onChange={(e) => setSelectedPlanId(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500 font-sans"
                  >
                    {plans.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} — ₹{p.plan_price} / {p.billing_interval} (Min Qty: {p.minimum_quantity})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">Proposal Validity (Days)</label>
                <input
                  type="number"
                  min="1"
                  value={expirationDays}
                  onChange={(e) => setExpirationDays(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* Dynamic Line Items Builder */}
              <div className="pt-2 border-t border-slate-800 space-y-3 font-sans">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-300 uppercase tracking-wider text-[11px]">
                    Quotation Line Items & Agreed Prices
                  </span>
                  <button
                    type="button"
                    onClick={addLineItem}
                    className="px-2.5 py-1 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 text-[11px] font-semibold hover:bg-indigo-900 transition flex items-center space-x-1"
                  >
                    <Plus className="w-3 h-3" />
                    <span>Add Item</span>
                  </button>
                </div>

                <div className="space-y-2">
                  {quoteItems.map((line, idx) => {
                    const selectedProd = products.find((p) => p.id === line.product_id);
                    const lineTotal = (parseFloat(line.unit_price) * line.quantity).toFixed(2);

                    return (
                      <div key={idx} className="flex items-center space-x-2 bg-slate-950 p-2 rounded-lg border border-slate-800">
                        {/* Select Product */}
                        <div className="flex-1">
                          <select
                            value={line.product_id}
                            onChange={(e) => updateLineProduct(idx, Number(e.target.value))}
                            className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-200 text-xs"
                          >
                            {products.map((p) => (
                              <option key={p.id} value={p.id}>
                                {p.name} (Base ₹{p.sales_price})
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Select Variant */}
                        <div className="w-36">
                          <select
                            value={line.variant_id || ''}
                            onChange={(e) => updateLineVariant(idx, e.target.value)}
                            className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-200 text-xs"
                          >
                            <option value="">Base (No Variant)</option>
                            {selectedProd?.variants.map((v) => (
                              <option key={v.id} value={v.id}>
                                {v.variant_name} (+₹{v.additional_price})
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Quantity */}
                        <div className="w-16">
                          <input
                            type="number"
                            min="1"
                            value={line.quantity}
                            onChange={(e) => updateLineQuantity(idx, Number(e.target.value))}
                            className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-200 font-mono text-xs text-center"
                          />
                        </div>

                        {/* Unit Price */}
                        <div className="w-24 text-right font-mono text-slate-300">
                          ₹{line.unit_price}
                        </div>

                        {/* Line Total */}
                        <div className="w-24 text-right font-mono font-bold text-emerald-400">
                          ₹{lineTotal}
                        </div>

                        {/* Remove line */}
                        <button
                          type="button"
                          onClick={() => removeLineItem(idx)}
                          className="p-1 text-slate-500 hover:text-rose-400"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    );
                  })}
                </div>

                {/* Subtotal preview */}
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between font-mono">
                  <span className="text-slate-400">Calculated Subtotal:</span>
                  <span className="text-emerald-400 font-bold text-base">₹{calculatedSubtotal.toFixed(2)}</span>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
                >
                  {submitting ? 'Generating...' : 'Issue Quotation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Quotation Details Modal */}
      {selectedQuote && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-4 text-slate-100">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="font-bold text-white text-base font-mono">
                  Quotation #{selectedQuote.quotation_number}
                </h3>
                <p className="text-xs text-slate-400 font-sans">
                  Issued to: {selectedQuote.customer_name} ({selectedQuote.customer_code})
                </p>
              </div>
              <button onClick={() => setSelectedQuote(null)} className="p-1 text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs font-mono">
              <div>
                <span className="text-slate-500 block text-[10px]">Plan:</span>
                <span className="text-white font-sans">{selectedQuote.plan_name}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">Quote Date:</span>
                <span className="text-slate-300">{new Date(selectedQuote.quotation_date).toLocaleDateString()}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">Expires:</span>
                <span className="text-amber-400">{new Date(selectedQuote.expiration_date).toLocaleDateString()}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">Status:</span>
                <span className="text-emerald-400 font-bold">{selectedQuote.status}</span>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                Quotation Line Items:
              </span>
              <table className="w-full text-left text-xs font-mono border border-slate-800 rounded-lg overflow-hidden">
                <thead className="bg-slate-950 text-slate-400">
                  <tr>
                    <th className="p-2">Item</th>
                    <th className="p-2">Variant</th>
                    <th className="p-2 text-center">Qty</th>
                    <th className="p-2 text-right">Unit Price</th>
                    <th className="p-2 text-right">Subtotal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                  {selectedQuote.items.map((it) => (
                    <tr key={it.id}>
                      <td className="p-2 font-sans font-medium text-white">{it.product_name}</td>
                      <td className="p-2 text-slate-400">{it.variant_name || '—'}</td>
                      <td className="p-2 text-center">{it.quantity}</td>
                      <td className="p-2 text-right">₹{it.unit_price}</td>
                      <td className="p-2 text-right font-bold text-emerald-400">₹{it.subtotal}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">Grand Total:</span>
              <span className="text-2xl font-bold text-emerald-400">₹{selectedQuote.total}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
