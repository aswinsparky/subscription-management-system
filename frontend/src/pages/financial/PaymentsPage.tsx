import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { 
  CreditCard, 
  Plus, 
  CheckCircle2, 
  XCircle, 
} from 'lucide-react';

interface Payment {
  id: number;
  payment_reference: string;
  invoice_id: number;
  customer_id: number;
  amount: number;
  payment_date: string;
  payment_method: string;
  payment_status: string;
  transaction_id: string | null;
  notes: string | null;
  created_at: string;
}

interface PaymentListResponse {
  items: Payment[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export function PaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRecordOpen, setIsRecordOpen] = useState(false);

  // Form
  const [invoiceId, setInvoiceId] = useState('');
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState('CARD');
  const [notes, setNotes] = useState('');
  const [simulateFailure, setSimulateFailure] = useState(false);

  const fetchPayments = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<PaymentListResponse>('/payments?page=1&page_size=25');
      setPayments(res.data.items);
    } catch (err) {
      console.error('Failed to load payments', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPayments();
  }, []);

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/payments', {
        invoice_id: parseInt(invoiceId),
        amount: parseFloat(amount),
        payment_method: method,
        notes: notes || undefined,
        simulate_failure: simulateFailure,
      });
      setIsRecordOpen(false);
      setInvoiceId('');
      setAmount('');
      setNotes('');
      setSimulateFailure(false);
      fetchPayments();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to record payment');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950/70 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <h2 className="text-xl font-extrabold text-white">Payment Management</h2>
          <p className="text-slate-400 text-xs mt-0.5">
            Record payments, partial settlements, simulated gateways, and transactional audit trails.
          </p>
        </div>
        <button
          onClick={() => setIsRecordOpen(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition"
        >
          <Plus className="w-4 h-4" />
          <span>Record Payment</span>
        </button>
      </div>

      {/* Payments Table */}
      <div className="bg-slate-950/60 rounded-2xl border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-5 py-3.5">Payment Ref</th>
                <th className="px-5 py-3.5">Invoice ID</th>
                <th className="px-5 py-3.5">Payment Date</th>
                <th className="px-5 py-3.5">Method</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5 text-right">Amount ($)</th>
                <th className="px-5 py-3.5">Transaction ID</th>
                <th className="px-5 py-3.5">Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {payments.length > 0 ? (
                payments.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-900/50 transition">
                    <td className="px-5 py-3.5 font-mono font-bold text-indigo-400">
                      {p.payment_reference}
                    </td>
                    <td className="px-5 py-3.5 font-mono text-slate-400">
                      #{p.invoice_id}
                    </td>
                    <td className="px-5 py-3.5 text-slate-400">
                      {new Date(p.payment_date).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="px-2 py-0.5 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 font-mono text-[11px]">
                        {p.payment_method}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      {p.payment_status === 'SUCCESSFUL' ? (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>SUCCESS</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          <XCircle className="w-3 h-3" />
                          <span>FAILED</span>
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono font-bold text-emerald-400">
                      ${Number(p.amount).toFixed(2)}
                    </td>
                    <td className="px-5 py-3.5 font-mono text-[11px] text-slate-400">
                      {p.transaction_id || 'N/A'}
                    </td>
                    <td className="px-5 py-3.5 text-slate-400 max-w-xs truncate">
                      {p.notes || '—'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-5 py-8 text-center text-slate-500">
                    {loading ? 'Loading payments...' : 'No payments recorded yet.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Record Payment Modal */}
      {isRecordOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <CreditCard className="w-4 h-4 text-indigo-400" />
              <span>Record Invoice Payment</span>
            </h3>

            <form onSubmit={handleRecordPayment} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Target Invoice ID</label>
                <input
                  type="number"
                  required
                  placeholder="e.g. 1"
                  value={invoiceId}
                  onChange={(e) => setInvoiceId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Payment Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  placeholder="e.g. 50.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Payment Method</label>
                <select
                  value={method}
                  onChange={(e) => setMethod(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                >
                  <option value="CARD">Credit / Debit Card</option>
                  <option value="BANK_TRANSFER">Bank Wire Transfer</option>
                  <option value="UPI">UPI Instant</option>
                  <option value="CASH">Cash Deposit</option>
                  <option value="SIMULATED">Simulated Gateway</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Audit Notes</label>
                <input
                  type="text"
                  placeholder="e.g. Wire transfer confirmed via Bank Statement"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                />
              </div>

              {/* Demo Failure Simulator Checkbox */}
              <div className="p-3 bg-rose-950/20 border border-rose-900/30 rounded-xl flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="simulateFailure"
                  checked={simulateFailure}
                  onChange={(e) => setSimulateFailure(e.target.checked)}
                  className="rounded text-rose-500 bg-slate-800 border-slate-700"
                />
                <label htmlFor="simulateFailure" className="text-[11px] text-rose-300">
                  Simulate Gateway Failure (Test Revenue Guardian & Recovery)
                </label>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3">
                <button
                  type="button"
                  onClick={() => setIsRecordOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition"
                >
                  Execute Payment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

