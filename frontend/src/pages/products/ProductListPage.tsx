import React, { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Product, ProductListResponse, Variant } from '../../types/product';
import { 
  Package, 
  Search, 
  Plus, 
  Trash2, 
  ChevronDown, 
  ChevronUp, 
  Layers, 
  X, 
  CheckCircle2, 
  AlertCircle, 
  Calculator,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

export const ProductListPage: React.FC = () => {
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [expandedProductIds, setExpandedProductIds] = useState<Set<number>>(new Set());

  // Modal states
  const [isAddProductOpen, setIsAddProductOpen] = useState<boolean>(false);
  const [selectedProductForVariant, setSelectedProductForVariant] = useState<Product | null>(null);

  // Form states for Product
  const [productForm, setProductForm] = useState({
    name: '',
    product_type: 'SOFTWARE',
    sales_price: '5000.00',
    cost_price: '2000.00',
    description: '',
    internal_notes: '',
    variants: [
      { variant_name: 'Standard', sku: '', additional_price: '0.00' },
      { variant_name: 'Odoo Edition', sku: '', additional_price: '560.00' },
      { variant_name: 'Enterprise Edition', sku: '', additional_price: '1200.00' },
    ],
  });

  // Form states for adding a single Variant
  const [variantForm, setVariantForm] = useState({
    variant_name: '',
    sku: '',
    additional_price: '0.00',
  });

  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<ProductListResponse>('/products/', {
        params: {
          query: searchQuery || undefined,
          product_type: typeFilter !== 'ALL' ? typeFilter : undefined,
          page,
          page_size: pageSize,
        },
      });
      setProducts(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [page, typeFilter]);

  const toggleExpand = (id: number) => {
    const next = new Set(expandedProductIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpandedProductIds(next);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchProducts();
  };

  // Dynamic initial variant manipulation
  const addVariantRow = () => {
    setProductForm({
      ...productForm,
      variants: [...productForm.variants, { variant_name: '', sku: '', additional_price: '0.00' }],
    });
  };

  const removeVariantRow = (index: number) => {
    const updated = [...productForm.variants];
    updated.splice(index, 1);
    setProductForm({ ...productForm, variants: updated });
  };

  const updateVariantRow = (index: number, field: string, val: string) => {
    const updated = [...productForm.variants];
    (updated[index] as any)[field] = val;
    setProductForm({ ...productForm, variants: updated });
  };

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);

    try {
      const payload = {
        name: productForm.name.trim(),
        product_type: productForm.product_type,
        sales_price: productForm.sales_price,
        cost_price: productForm.cost_price,
        description: productForm.description.trim() || undefined,
        internal_notes: productForm.internal_notes.trim() || undefined,
        variants: productForm.variants
          .filter((v) => v.variant_name.trim().length > 0)
          .map((v) => ({
            variant_name: v.variant_name.trim(),
            sku: v.sku.trim() || undefined,
            additional_price: v.additional_price || '0.00',
          })),
      };

      await apiClient.post('/products/', payload);
      setFormSuccess('Product and variants created successfully.');
      setTimeout(() => {
        setIsAddProductOpen(false);
        fetchProducts();
      }, 1200);
    } catch (err: any) {
      setFormError(err?.response?.data?.detail || 'Failed to create product.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddSingleVariant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductForVariant) return;
    setFormError(null);
    setSubmitting(true);

    try {
      await apiClient.post(`/products/${selectedProductForVariant.id}/variants`, {
        variant_name: variantForm.variant_name.trim(),
        sku: variantForm.sku.trim() || undefined,
        additional_price: variantForm.additional_price || '0.00',
      });
      setFormSuccess('Variant added successfully.');
      setTimeout(() => {
        setSelectedProductForVariant(null);
        fetchProducts();
      }, 1200);
    } catch (err: any) {
      setFormError(err?.response?.data?.detail || 'Failed to add variant.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteProduct = async (prod: Product) => {
    if (!window.confirm(`Are you sure you want to delete or archive product '${prod.name}'?`)) {
      return;
    }
    try {
      const res = await apiClient.delete<{ message: string; action: string }>(`/products/${prod.id}`);
      alert(res.data.message);
      fetchProducts();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to delete product.');
    }
  };

  const canManageProducts = user?.role === 'ADMIN' || user?.role === 'STAFF';

  return (
    <div className="space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center space-x-2.5">
            <Package className="w-6 h-6 text-indigo-400" />
            <span>Product Catalog & Variant Pricing</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Base products, multi-variant pricing engine: Final Price = Base Price + Variant Additional Price
          </p>
        </div>

        {canManageProducts && (
          <button
            onClick={() => {
              setProductForm({
                name: '',
                product_type: 'SOFTWARE',
                sales_price: '5000.00',
                cost_price: '2000.00',
                description: '',
                internal_notes: '',
                variants: [
                  { variant_name: 'Standard', sku: '', additional_price: '0.00' },
                  { variant_name: 'Odoo Edition', sku: '', additional_price: '560.00' },
                  { variant_name: 'Enterprise Edition', sku: '', additional_price: '1200.00' },
                ],
              });
              setFormError(null);
              setFormSuccess(null);
              setIsAddProductOpen(true);
            }}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>Add New Product</span>
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
            placeholder="Search by product name, code, description..."
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
          />
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
        </form>

        <div className="flex items-center space-x-2 w-full md:w-auto">
          <span className="text-xs font-medium text-slate-400 whitespace-nowrap">Category:</span>
          <div className="flex items-center space-x-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs overflow-x-auto">
            {['ALL', 'SOFTWARE', 'SERVICE', 'HARDWARE', 'CONSUMABLE'].map((tp) => (
              <button
                key={tp}
                onClick={() => {
                  setTypeFilter(tp);
                  setPage(1);
                }}
                className={`px-3 py-1 rounded-md text-[11px] font-semibold transition whitespace-nowrap ${
                  typeFilter === tp
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tp}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-slate-950/80 rounded-xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 w-8"></th>
                <th className="py-3 px-4">Product Code</th>
                <th className="py-3 px-4">Name & Category</th>
                <th className="py-3 px-4">Base Sales Price</th>
                <th className="py-3 px-4">Cost Price</th>
                <th className="py-3 px-4">Variants</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    Loading product catalog...
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    No products found in this category.
                  </td>
                </tr>
              ) : (
                products.map((p) => {
                  const isExpanded = expandedProductIds.has(p.id);
                  return (
                    <React.Fragment key={p.id}>
                      <tr className="hover:bg-slate-900/40 transition">
                        <td className="py-3 px-4">
                          <button
                            onClick={() => toggleExpand(p.id)}
                            className="p-1 rounded text-slate-400 hover:text-white"
                          >
                            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </td>
                        <td className="py-3 px-4 font-bold text-indigo-400">{p.product_code}</td>
                        <td className="py-3 px-4 font-sans">
                          <div className="font-semibold text-white">{p.name}</div>
                          <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-slate-900 text-indigo-300 border border-slate-800">
                            {p.product_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-bold text-emerald-400">₹{p.sales_price}</td>
                        <td className="py-3 px-4 text-slate-400">₹{p.cost_price}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300 text-[11px]">
                            {p.variants.length} variant{p.variants.length === 1 ? '' : 's'}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              p.is_active
                                ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                                : 'bg-rose-950 text-rose-300 border border-rose-800'
                            }`}
                          >
                            {p.is_active ? 'ACTIVE' : 'ARCHIVED'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right space-x-2 font-sans">
                          {canManageProducts && (
                            <>
                              <button
                                onClick={() => {
                                  setSelectedProductForVariant(p);
                                  setVariantForm({ variant_name: '', sku: '', additional_price: '0.00' });
                                  setFormError(null);
                                  setFormSuccess(null);
                                }}
                                className="px-2 py-1 rounded bg-indigo-950 hover:bg-indigo-900 text-indigo-300 border border-indigo-800 text-[11px] font-medium transition inline-flex items-center space-x-1"
                              >
                                <Plus className="w-3 h-3" />
                                <span>Add Variant</span>
                              </button>
                              <button
                                onClick={() => handleDeleteProduct(p)}
                                title="Delete or Archive Product"
                                className="px-2 py-1 rounded bg-slate-900 hover:bg-rose-950 text-rose-400 border border-slate-800 hover:border-rose-800 text-[11px] font-medium transition inline-flex items-center space-x-1"
                              >
                                <Trash2 className="w-3 h-3" />
                                <span>Delete/Archive</span>
                              </button>
                            </>
                          )}
                        </td>
                      </tr>

                      {/* Expandable Variants Drawer */}
                      {isExpanded && (
                        <tr className="bg-slate-950/90 border-b border-slate-800/80">
                          <td colSpan={8} className="p-4 pl-12 space-y-3 font-sans">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
                                <Layers className="w-4 h-4 text-indigo-400" />
                                <span>Pricing Tiers & Variants for {p.name}:</span>
                              </div>
                              <span className="text-[11px] text-slate-500 font-mono">
                                Formula: Final Line Price = Base Sales Price (₹{p.sales_price}) + Variant Surcharge
                              </span>
                            </div>

                            {p.variants.length === 0 ? (
                              <p className="text-xs text-slate-500 italic bg-slate-900 p-3 rounded-lg border border-slate-800">
                                No specific variants configured for this product. Defaulting to base price.
                              </p>
                            ) : (
                              <div className="overflow-x-auto">
                                <table className="w-full text-left text-xs font-mono border border-slate-800/80 rounded-lg overflow-hidden">
                                  <thead className="bg-slate-900 text-slate-400">
                                    <tr>
                                      <th className="p-2">Variant Name</th>
                                      <th className="p-2">SKU</th>
                                      <th className="p-2">Base Price</th>
                                      <th className="p-2">Additional Surcharge</th>
                                      <th className="p-2 text-emerald-400">Final Computed Price</th>
                                      <th className="p-2">Status</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                                    {p.variants.map((v: Variant) => (
                                      <tr key={v.id}>
                                        <td className="p-2 font-bold text-white font-sans">{v.variant_name}</td>
                                        <td className="p-2 text-slate-400">{v.sku || '—'}</td>
                                        <td className="p-2 text-slate-300">₹{p.sales_price}</td>
                                        <td className="p-2 text-amber-400">+ ₹{v.additional_price}</td>
                                        <td className="p-2 font-bold text-emerald-400 text-sm">₹{v.final_price}</td>
                                        <td className="p-2">
                                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800">
                                            ACTIVE
                                          </span>
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>Showing {products.length} of {total} products</span>
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

      {/* Add Product Modal with Dynamic Variant Builder */}
      {isAddProductOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-4 text-slate-100">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-white text-base flex items-center space-x-2">
                <Package className="w-5 h-5 text-indigo-400" />
                <span>Create New Product & Configure Variants</span>
              </h3>
              <button
                onClick={() => setIsAddProductOpen(false)}
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

            <form onSubmit={handleCreateProduct} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Product Name *</label>
                  <input
                    type="text"
                    required
                    value={productForm.name}
                    onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
                    placeholder="e.g. Enterprise Business Software"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Product Type *</label>
                  <select
                    value={productForm.product_type}
                    onChange={(e) => setProductForm({ ...productForm, product_type: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                  >
                    <option value="SOFTWARE">SOFTWARE</option>
                    <option value="SERVICE">SERVICE</option>
                    <option value="HARDWARE">HARDWARE</option>
                    <option value="CONSUMABLE">CONSUMABLE</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Base Sales Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={productForm.sales_price}
                    onChange={(e) => setProductForm({ ...productForm, sales_price: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Cost Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={productForm.cost_price}
                    onChange={(e) => setProductForm({ ...productForm, cost_price: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Description</label>
                <textarea
                  rows={2}
                  value={productForm.description}
                  onChange={(e) => setProductForm({ ...productForm, description: e.target.value })}
                  placeholder="Product description for quotation documents..."
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* Dynamic Variants Builder Section */}
              <div className="pt-2 border-t border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1.5">
                    <Calculator className="w-4 h-4 text-indigo-400" />
                    <span className="text-xs font-semibold text-white uppercase tracking-wider">
                      Product Variants & Pricing Surcharges
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={addVariantRow}
                    className="px-2.5 py-1 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 text-[11px] font-semibold hover:bg-indigo-900 transition flex items-center space-x-1"
                  >
                    <Plus className="w-3 h-3" />
                    <span>Add Variant Row</span>
                  </button>
                </div>

                <div className="space-y-2">
                  {productForm.variants.map((v, idx) => {
                    const basePriceNum = parseFloat(productForm.sales_price) || 0;
                    const addPriceNum = parseFloat(v.additional_price) || 0;
                    const finalComputed = (basePriceNum + addPriceNum).toFixed(2);

                    return (
                      <div key={idx} className="flex items-center space-x-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-xs">
                        <div className="flex-1">
                          <input
                            type="text"
                            placeholder="Variant Name (e.g. Odoo Edition)"
                            value={v.variant_name}
                            onChange={(e) => updateVariantRow(idx, 'variant_name', e.target.value)}
                            className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div className="w-32">
                          <input
                            type="text"
                            placeholder="SKU (optional)"
                            value={v.sku}
                            onChange={(e) => updateVariantRow(idx, 'sku', e.target.value)}
                            className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-200 text-xs font-mono focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div className="w-28">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            placeholder="+ Surcharge"
                            value={v.additional_price}
                            onChange={(e) => updateVariantRow(idx, 'additional_price', e.target.value)}
                            className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-800 text-amber-400 font-mono text-xs focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div className="w-24 text-right font-mono font-bold text-emerald-400">
                          ₹{finalComputed}
                        </div>
                        <button
                          type="button"
                          onClick={() => removeVariantRow(idx)}
                          className="p-1 rounded text-slate-500 hover:text-rose-400"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddProductOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
                >
                  <span>{submitting ? 'Creating Product...' : 'Save Product & Variants'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Single Variant Modal */}
      {selectedProductForVariant && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-4 text-slate-100">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-white text-base">
                Add Variant to {selectedProductForVariant.name}
              </h3>
              <button
                onClick={() => setSelectedProductForVariant(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formSuccess && (
              <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs">
                {formSuccess}
              </div>
            )}

            {formError && (
              <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
                {formError}
              </div>
            )}

            <form onSubmit={handleAddSingleVariant} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">Variant Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Platinum Edition"
                  value={variantForm.variant_name}
                  onChange={(e) => setVariantForm({ ...variantForm, variant_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">SKU (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. PLAT-001"
                  value={variantForm.sku}
                  onChange={(e) => setVariantForm({ ...variantForm, sku: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">Additional Surcharge (₹) *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={variantForm.additional_price}
                  onChange={(e) => setVariantForm({ ...variantForm, additional_price: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-amber-400 font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex items-center justify-between font-mono">
                <span className="text-slate-400 text-[11px]">Final Computed Price:</span>
                <span className="text-emerald-400 font-bold">
                  ₹{(parseFloat(selectedProductForVariant.sales_price) + (parseFloat(variantForm.additional_price) || 0)).toFixed(2)}
                </span>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedProductForVariant(null)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
                >
                  {submitting ? 'Adding...' : 'Add Variant'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
