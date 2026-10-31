import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { 
  Percent, 
  Tag, 
  Plus, 
} from 'lucide-react';

interface Tax {
  id: number;
  name: string;
  description: string | null;
  tax_type: string;
  rate: number;
  applicability: string;
  is_active: boolean;
}

interface Discount {
  id: number;
  name: string;
  coupon_code: string;
  discount_type: string;
  discount_value: number;
  min_purchase_amount: number;
  max_usage_limit: number | null;
  current_usage_count: number;
  is_active: boolean;
}

export function TaxesDiscountsPage() {
  const { user } = useAuth();
  const [taxes, setTaxes] = useState<Tax[]>([]);
  const [discounts, setDiscounts] = useState<Discount[]>([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isTaxModalOpen, setIsTaxModalOpen] = useState(false);
  const [isDiscountModalOpen, setIsDiscountModalOpen] = useState(false);

  // Tax form
  const [taxName, setTaxName] = useState('');
  const [taxType, setTaxType] = useState('PERCENTAGE');
  const [taxRate, setTaxRate] = useState('');

  // Discount form
  const [discountName, setDiscountName] = useState('');
  const [couponCode, setCouponCode] = useState('');
  const [discountType, setDiscountType] = useState('PERCENTAGE');
  const [discountVal, setDiscountVal] = useState('');
  const [minPurchase, setMinPurchase] = useState('0');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [tRes, dRes] = await Promise.all([
        apiClient.get<Tax[]>('/taxes'),
        apiClient.get<Discount[]>('/discounts'),
      ]);
      setTaxes(tRes.data);
      setDiscounts(dRes.data);
    } catch (err) {
      console.error('Failed to load taxes or discounts', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateTax = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/taxes', {
        name: taxName,
        tax_type: taxType,
        rate: parseFloat(taxRate),
        applicability: 'ALL',
      });
      setIsTaxModalOpen(false);
      setTaxName('');
      setTaxRate('');
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to create tax rule');
    }
  };

  const handleCreateDiscount = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/discounts', {
        name: discountName,
        coupon_code: couponCode,
        discount_type: discountType,
        discount_value: parseFloat(discountVal),
        min_purchase_amount: parseFloat(minPurchase),
      });
      setIsDiscountModalOpen(false);
      setDiscountName('');
      setCouponCode('');
      setDiscountVal('');
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to create discount');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 1. Tax Management Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between bg-slate-950/70 p-5 rounded-2xl border border-slate-800">
          <div>
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <Percent className="w-4 h-4 text-indigo-400" />
              <span>Tax Configuration (Module 1)</span>
            </h2>
            <p className="text-slate-400 text-xs">
              Configurable percentage and fixed rate taxes preserved on confirmed invoices.
            </p>
          </div>
          {user?.role === 'ADMIN' && (
            <button
              onClick={() => setIsTaxModalOpen(true)}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl transition shadow-md shadow-indigo-600/30"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Tax</span>
            </button>
          )}
        </div>

        <div className="bg-slate-950/60 rounded-2xl border border-slate-800/80 overflow-hidden shadow-lg">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-5 py-3">Tax Name</th>
                <th className="px-5 py-3">Type</th>
                <th className="px-5 py-3">Rate</th>
                <th className="px-5 py-3">Applicability</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {taxes.map((t) => (
                <tr key={t.id} className="hover:bg-slate-900/50">
                  <td className="px-5 py-3 font-semibold text-white">{t.name}</td>
                  <td className="px-5 py-3 font-mono text-[11px] text-slate-400">{t.tax_type}</td>
                  <td className="px-5 py-3 font-mono font-bold text-indigo-400">
                    {t.tax_type === 'PERCENTAGE' ? `${Number(t.rate)}%` : `$${Number(t.rate).toFixed(2)}`}
                  </td>
                  <td className="px-5 py-3 text-slate-400">{t.applicability}</td>
                  <td className="px-5 py-3">
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      ACTIVE
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. Discount & Coupon Management Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between bg-slate-950/70 p-5 rounded-2xl border border-slate-800">
          <div>
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <Tag className="w-4 h-4 text-emerald-400" />
              <span>Discount & Coupon Codes (Module 2)</span>
            </h2>
            <p className="text-slate-400 text-xs">
              Promotional coupons with minimum purchase rules and customer usage limit enforcement.
            </p>
          </div>
          {user?.role === 'ADMIN' && (
            <button
              onClick={() => setIsDiscountModalOpen(true)}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl transition shadow-md shadow-emerald-600/30"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Coupon</span>
            </button>
          )}
        </div>

        <div className="bg-slate-950/60 rounded-2xl border border-slate-800/80 overflow-hidden shadow-lg">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-5 py-3">Discount Name</th>
                <th className="px-5 py-3">Coupon Code</th>
                <th className="px-5 py-3">Type</th>
                <th className="px-5 py-3">Value</th>
                <th className="px-5 py-3">Min Purchase</th>
                <th className="px-5 py-3">Usage Count</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {discounts.map((d) => (
                <tr key={d.id} className="hover:bg-slate-900/50">
                  <td className="px-5 py-3 font-semibold text-white">{d.name}</td>
                  <td className="px-5 py-3 font-mono font-bold text-emerald-400 bg-emerald-950/20 px-2 rounded">
                    {d.coupon_code}
                  </td>
                  <td className="px-5 py-3 font-mono text-[11px] text-slate-400">{d.discount_type}</td>
                  <td className="px-5 py-3 font-mono font-bold text-indigo-400">
                    {d.discount_type === 'PERCENTAGE' ? `${Number(d.discount_value)}%` : `$${Number(d.discount_value).toFixed(2)}`}
                  </td>
                  <td className="px-5 py-3 font-mono text-slate-400">${Number(d.min_purchase_amount).toFixed(2)}</td>
                  <td className="px-5 py-3 font-mono text-slate-300 font-semibold">
                    {d.current_usage_count} {d.max_usage_limit ? `/ ${d.max_usage_limit}` : 'uses'}
                  </td>
                  <td className="px-5 py-3">
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      ACTIVE
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Tax Modal */}
      {isTaxModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">Create Tax Rule</h3>
            <form onSubmit={handleCreateTax} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Tax Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. State VAT"
                  value={taxName}
                  onChange={(e) => setTaxName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Tax Type</label>
                <select
                  value={taxType}
                  onChange={(e) => setTaxType(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                >
                  <option value="PERCENTAGE">Percentage (%)</option>
                  <option value="FIXED">Fixed Amount ($)</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Rate</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="18.00"
                  value={taxRate}
                  onChange={(e) => setTaxRate(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsTaxModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white font-semibold rounded-xl"
                >
                  Save Tax
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Discount Modal */}
      {isDiscountModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">Create Discount Coupon</h3>
            <form onSubmit={handleCreateDiscount} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Discount Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Winter Holiday Special"
                  value={discountName}
                  onChange={(e) => setDiscountName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Coupon Code</label>
                <input
                  type="text"
                  required
                  placeholder="WINTER25"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 uppercase font-mono"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-400 mb-1">Type</label>
                  <select
                    value={discountType}
                    onChange={(e) => setDiscountType(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                  >
                    <option value="PERCENTAGE">Percent (%)</option>
                    <option value="FIXED">Fixed ($)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Value</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="25.00"
                    value={discountVal}
                    onChange={(e) => setDiscountVal(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                  />
                </div>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Minimum Purchase ($)</label>
                <input
                  type="number"
                  step="0.01"
                  value={minPurchase}
                  onChange={(e) => setMinPurchase(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-200"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsDiscountModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 text-white font-semibold rounded-xl"
                >
                  Save Coupon
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

