import { useState, useEffect, useRef } from 'react';
import Layout from '../components/Layout';
import { extractPdf, createProduct, listProducts, deleteProduct, updateProduct } from '../api/products';
import type { ExtractionReview, ProductCreate } from '../api/products';
import { createMealEntry } from '../api/meals';
import type { Product, MealType } from '../types';
import { formatServingLabel, getSuggestedMealType, sortProducts } from '../utils/mealUtils';

// ── Nutrient field helpers ────────────────────────────────────────────────────

const NUM_FIELDS: Array<{ key: keyof ProductCreate; label: string; unit: string; required?: boolean }> = [
  { key: 'serving_size_g', label: 'Serving size', unit: 'g', required: true },
  { key: 'calories', label: 'Calories', unit: 'kcal', required: true },
  { key: 'protein_g', label: 'Protein', unit: 'g', required: true },
  { key: 'carbs_g', label: 'Carbohydrates', unit: 'g', required: true },
  { key: 'fat_g', label: 'Fat', unit: 'g', required: true },
  { key: 'sugar_g', label: 'Sugar', unit: 'g' },
  { key: 'fiber_g', label: 'Fiber', unit: 'g' },
  { key: 'sodium_mg', label: 'Sodium', unit: 'mg' },
];

// ── Shared Modal Shell ────────────────────────────────────────────────────────

function ModalShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div role="dialog" aria-modal="true" className="bg-dark-800 border border-white/[0.08] rounded-2xl shadow-glass w-full max-w-lg max-h-[90vh] overflow-y-auto animate-fade-up">
        {children}
      </div>
    </div>
  );
}

// ── Upload + Review Modal ─────────────────────────────────────────────────────

function ReviewModal({
  review,
  onSave,
  onCancel,
  saving = false,
  saveError = '',
}: {
  review: ExtractionReview;
  onSave: (data: ProductCreate) => void;
  onCancel: () => void;
  saving?: boolean;
  saveError?: string;
}) {
  const [name, setName] = useState(review.suggested_name || '');
  const [brand, setBrand] = useState(review.suggested_brand || '');
  const [servingQuantity, setServingQuantity] = useState(
    review.extracted.serving_quantity != null ? String(review.extracted.serving_quantity) : ''
  );
  const [servingUnit, setServingUnit] = useState(review.extracted.serving_unit || '');
  const [values, setValues] = useState<Record<string, string>>({
    serving_size_g: String(review.extracted.serving_size_g),
    calories: String(review.extracted.calories),
    protein_g: String(review.extracted.protein_g),
    carbs_g: String(review.extracted.carbs_g),
    fat_g: String(review.extracted.fat_g),
    sugar_g: review.extracted.sugar_g != null ? String(review.extracted.sugar_g) : '',
    fiber_g: review.extracted.fiber_g != null ? String(review.extracted.fiber_g) : '',
    sodium_mg: review.extracted.sodium_mg != null ? String(review.extracted.sodium_mg) : '',
  });

  const confStyle = review.confidence === 'high'
    ? 'bg-brand-500/15 text-brand-400 border-brand-500/30'
    : review.confidence === 'medium'
    ? 'bg-accent-yellow-dim text-accent-yellow border-accent-yellow/30'
    : 'bg-red-900/30 text-red-400 border-red-800/50';

  const handleSave = () => {
    if (!name.trim()) return;
    const data: ProductCreate = {
      name: name.trim(),
      brand: brand.trim() || undefined,
      serving_size_g: parseFloat(values.serving_size_g) || 0,
      serving_quantity: servingQuantity ? parseFloat(servingQuantity) : undefined,
      serving_unit: servingUnit.trim() || undefined,
      calories: parseFloat(values.calories) || 0,
      protein_g: parseFloat(values.protein_g) || 0,
      carbs_g: parseFloat(values.carbs_g) || 0,
      fat_g: parseFloat(values.fat_g) || 0,
      sugar_g: values.sugar_g ? parseFloat(values.sugar_g) : undefined,
      fiber_g: values.fiber_g ? parseFloat(values.fiber_g) : undefined,
      sodium_mg: values.sodium_mg ? parseFloat(values.sodium_mg) : undefined,
    };
    onSave(data);
  };

  return (
    <ModalShell>
      <div className="p-6 border-b border-white/[0.06]">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-lg font-bold text-white">Review Extracted Data</h2>
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium border ${confStyle}`}>
            {review.confidence} confidence
          </span>
        </div>
        <p className="text-sm text-gray-500">Verify and correct before saving.</p>
      </div>

      <div className="p-6 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <label className="label-dark">Product name *</label>
            <input value={name} onChange={(e) => setName(e.target.value)}
              className="input-dark"
              placeholder="e.g. Gold Standard Whey" />
          </div>
          <div className="col-span-2">
            <label className="label-dark">Brand</label>
            <input value={brand} onChange={(e) => setBrand(e.target.value)}
              className="input-dark"
              placeholder="e.g. Optimum Nutrition" />
          </div>
          <div>
            <label className="label-dark">Serving quantity</label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={servingQuantity}
              onChange={(e) => setServingQuantity(e.target.value)}
              className="input-dark"
              placeholder="e.g. 2"
            />
          </div>
          <div>
            <label className="label-dark">Serving unit</label>
            <input
              value={servingUnit}
              onChange={(e) => setServingUnit(e.target.value)}
              className="input-dark"
              placeholder="e.g. egg, slice"
            />
          </div>
          {NUM_FIELDS.map((f) => (
            <div key={String(f.key)}>
              <label className="label-dark">
                {f.label} ({f.unit}){f.required && ' *'}
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={values[String(f.key)]}
                onChange={(e) => setValues((v) => ({ ...v, [String(f.key)]: e.target.value }))}
                className="input-dark"
              />
            </div>
          ))}
        </div>

        <details className="text-xs text-gray-600 cursor-pointer group">
          <summary className="hover:text-gray-400 transition-colors">Raw extracted text snippet</summary>
          <pre className="mt-2 bg-dark-900/60 border border-white/[0.05] rounded-xl p-3 whitespace-pre-wrap text-gray-500 max-h-32 overflow-y-auto font-mono text-[11px]">
            {review.raw_text_snippet}
          </pre>
        </details>
      </div>

      {saveError && (
        <div role="alert" className="mx-6 mb-2 bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm">
          {saveError}
        </div>
      )}
      <div className="p-6 border-t border-white/[0.06] flex gap-3">
        <button onClick={onCancel} className="btn-secondary flex-1">Cancel</button>
        <button onClick={handleSave} disabled={!name.trim() || saving} className="btn-primary flex-1 flex items-center justify-center gap-2">
          {saving ? (
            <>
              <svg className="animate-spin w-4 h-4" aria-hidden="true" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Saving…
            </>
          ) : 'Save product'}
        </button>
      </div>
    </ModalShell>
  );
}

// ── Manual Add Modal ──────────────────────────────────────────────────────────

function ManualModal({ onSave, onCancel, saving = false, saveError = '' }: {
  onSave: (d: ProductCreate) => void;
  onCancel: () => void;
  saving?: boolean;
  saveError?: string;
}) {
  const [name, setName] = useState('');
  const [brand, setBrand] = useState('');
  const [servingQuantity, setServingQuantity] = useState('');
  const [servingUnit, setServingUnit] = useState('');
  const [values, setValues] = useState<Record<string, string>>({
    serving_size_g: '', calories: '', protein_g: '', carbs_g: '',
    fat_g: '', sugar_g: '', fiber_g: '', sodium_mg: '',
  });

  const handleSave = () => {
    if (!name.trim() || !values.serving_size_g || !values.calories) return;
    onSave({
      name: name.trim(), brand: brand.trim() || undefined,
      serving_size_g: parseFloat(values.serving_size_g),
      serving_quantity: servingQuantity ? parseFloat(servingQuantity) : undefined,
      serving_unit: servingUnit.trim() || undefined,
      calories: parseFloat(values.calories),
      protein_g: parseFloat(values.protein_g) || 0,
      carbs_g: parseFloat(values.carbs_g) || 0,
      fat_g: parseFloat(values.fat_g) || 0,
      sugar_g: values.sugar_g ? parseFloat(values.sugar_g) : undefined,
      fiber_g: values.fiber_g ? parseFloat(values.fiber_g) : undefined,
      sodium_mg: values.sodium_mg ? parseFloat(values.sodium_mg) : undefined,
    });
  };

  return (
    <ModalShell>
      <div className="p-6 border-b border-white/[0.06]">
        <h2 className="text-lg font-bold text-white">Add Product Manually</h2>
        <p className="text-sm text-gray-500 mt-0.5">Enter nutrition info from the product label</p>
      </div>
      <div className="p-6 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <label className="label-dark">Product name *</label>
            <input value={name} onChange={(e) => setName(e.target.value)} className="input-dark" placeholder="e.g. Gold Standard Whey" />
          </div>
          <div className="col-span-2">
            <label className="label-dark">Brand</label>
            <input value={brand} onChange={(e) => setBrand(e.target.value)} className="input-dark" placeholder="e.g. Optimum Nutrition" />
          </div>
          <div>
            <label className="label-dark">Serving quantity</label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={servingQuantity}
              onChange={(e) => setServingQuantity(e.target.value)}
              className="input-dark"
              placeholder="e.g. 2"
            />
          </div>
          <div>
            <label className="label-dark">Serving unit</label>
            <input
              value={servingUnit}
              onChange={(e) => setServingUnit(e.target.value)}
              className="input-dark"
              placeholder="e.g. egg, slice"
            />
          </div>
          {NUM_FIELDS.map((f) => (
            <div key={String(f.key)}>
              <label className="label-dark">{f.label} ({f.unit}){f.required && ' *'}</label>
              <input type="number" step="0.1" min="0"
                value={values[String(f.key)]}
                onChange={(e) => setValues((v) => ({ ...v, [String(f.key)]: e.target.value }))}
                className="input-dark" />
            </div>
          ))}
        </div>
      </div>
      {saveError && (
        <div role="alert" className="mx-6 mb-2 bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm">
          {saveError}
        </div>
      )}
      <div className="p-6 border-t border-white/[0.06] flex gap-3">
        <button onClick={onCancel} className="btn-secondary flex-1">Cancel</button>
        <button onClick={handleSave} disabled={!name.trim() || saving} className="btn-primary flex-1 flex items-center justify-center gap-2">
          {saving ? (
            <>
              <svg className="animate-spin w-4 h-4" aria-hidden="true" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Saving…
            </>
          ) : 'Save product'}
        </button>
      </div>
    </ModalShell>
  );
}

function QuickLogModal({
  product,
  onClose,
  onLogged,
}: {
  product: Product;
  onClose: () => void;
  onLogged: () => void;
}) {
  const [mealType, setMealType] = useState<MealType>(getSuggestedMealType);
  const [quantity, setQuantity] = useState(product.serving_quantity ? String(product.serving_quantity) : '1');
  const [unit, setUnit] = useState(product.serving_unit || 'serving');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleLog = async () => {
    setSaving(true);
    setError('');
    try {
      await createMealEntry({
        meal_type: mealType,
        raw_text: `${quantity || '1'} ${unit || 'serving'} ${product.name}`,
        items: [
          {
            product_id: product.id,
            quantity: parseFloat(quantity) || 1,
            unit: unit.trim() || 'serving',
          },
        ],
      });
      onLogged();
      onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Failed to log product');
    } finally {
      setSaving(false);
    }
  };

  return (
    <ModalShell>
      <div className="p-6 border-b border-white/[0.06]">
        <h2 className="text-lg font-bold text-white">Quick Log Product</h2>
        <p className="text-sm text-gray-500 mt-0.5">Choose the meal and quantity for this product.</p>
      </div>

      <div className="p-6 space-y-5">
        <div className="glass-card rounded-2xl p-4">
          <div className="text-base font-semibold text-gray-100">{product.name}</div>
          {product.brand && <div className="text-sm text-gray-500 mt-1">{product.brand}</div>}
          <div className="text-sm text-accent-orange font-semibold mt-3">
            {Math.round(product.calories)} kcal per {formatServingLabel(product)}
          </div>
        </div>

        <div>
          <label className="label-dark">Meal</label>
          <div className="grid grid-cols-2 gap-2">
            {(['breakfast', 'lunch', 'dinner', 'snack'] as MealType[]).map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setMealType(type)}
                className={`rounded-xl px-3 py-2 text-sm font-medium transition-all ${
                  mealType === type
                    ? 'bg-brand-500/20 text-brand-400 border border-brand-500/40'
                    : 'bg-dark-700 text-gray-400 border border-transparent hover:text-gray-200 hover:border-white/[0.08]'
                }`}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label-dark">Quantity</label>
            <input
              type="number"
              min="0.1"
              step="0.1"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="input-dark"
            />
          </div>
          <div>
            <label className="label-dark">Unit</label>
            <input
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              className="input-dark"
              placeholder="serving"
            />
          </div>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm">
            {error}
          </div>
        )}
      </div>

      <div className="p-6 border-t border-white/[0.06] flex gap-3">
        <button onClick={onClose} className="btn-secondary flex-1">Cancel</button>
        <button onClick={handleLog} disabled={saving} className="btn-primary flex-1">
          {saving ? 'Logging...' : 'Add to Meal'}
        </button>
      </div>
    </ModalShell>
  );
}

// ── Product Card ──────────────────────────────────────────────────────────────

function ProductCard({
  product,
  onDelete,
  onSelect,
  onToggleFavorite,
}: {
  product: Product;
  onDelete: (id: string) => void;
  onSelect: (product: Product) => void;
  onToggleFavorite: (product: Product) => void;
}) {
  const [confirming, setConfirming] = useState(false);

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onSelect(product)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(product);
        }
      }}
      className="glass-card-hover rounded-2xl p-5 animate-fade-up group cursor-pointer"
    >
      {/* Name + calories */}
      <div className="flex items-start justify-between mb-3">
        <div className="min-w-0 flex-1 pr-3">
          <div className="flex items-start gap-2">
            <button
              type="button"
              aria-label={product.is_favorite ? `Unstar ${product.name}` : `Star ${product.name}`}
              title={product.is_favorite ? 'Remove star' : 'Star product'}
              onClick={(e) => {
                e.stopPropagation();
                onToggleFavorite(product);
              }}
              className={`mt-0.5 rounded-lg border px-2 py-1 text-sm leading-none transition-colors ${
                product.is_favorite
                  ? 'border-accent-yellow/40 bg-accent-yellow/15 text-accent-yellow'
                  : 'border-white/[0.08] bg-dark-700/50 text-gray-500 hover:text-accent-yellow hover:border-accent-yellow/30'
              }`}
            >
              {product.is_favorite ? '★' : '☆'}
            </button>
            <div className="min-w-0">
              <div className="font-semibold text-gray-100 text-sm leading-snug">{product.name}</div>
              {product.brand && <div className="text-xs text-gray-500 mt-0.5">{product.brand}</div>}
            </div>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-xl font-bold text-accent-orange tabular-nums">{Math.round(product.calories)}</div>
          <div className="text-xs text-gray-600">kcal / {formatServingLabel(product)}</div>
        </div>
      </div>

      {/* Macro pills */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        <span className="flex items-center gap-1 bg-accent-blue/10 border border-accent-blue/20 text-accent-blue text-xs px-2 py-0.5 rounded-lg font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-accent-blue" />
          P {product.protein_g}g
        </span>
        <span className="flex items-center gap-1 bg-accent-yellow/10 border border-accent-yellow/20 text-accent-yellow text-xs px-2 py-0.5 rounded-lg font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-accent-yellow" />
          C {product.carbs_g}g
        </span>
        <span className="flex items-center gap-1 bg-accent-purple/10 border border-accent-purple/20 text-accent-purple text-xs px-2 py-0.5 rounded-lg font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-accent-purple" />
          F {product.fat_g}g
        </span>
        {product.fiber_g != null && (
          <span className="flex items-center gap-1 bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs px-2 py-0.5 rounded-lg">
            Fiber {product.fiber_g}g
          </span>
        )}
      </div>

      {/* Delete */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onSelect(product);
          }}
          className="text-sm text-brand-400 hover:text-brand-300 font-medium transition-colors"
        >
          Quick add
        </button>
        {confirming ? (
          <div className="flex gap-3 text-xs">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setConfirming(false);
              }}
              className="text-gray-500 hover:text-gray-300 transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(product.id);
              }}
              className="text-red-400 hover:text-red-300 font-semibold transition-colors"
            >
              Delete
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setConfirming(true);
            }}
            className="text-xs text-gray-700 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [search, setSearch] = useState('');
  const [review, setReview] = useState<ExtractionReview | null>(null);
  const [showManual, setShowManual] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const [favoriteError, setFavoriteError] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const load = async () => {
    setLoadError('');
    try {
      const r = await listProducts();
      setProducts(sortProducts(r.data));
    } catch {
      setLoadError('Failed to load products. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';
    setUploadError('');
    setUploading(true);
    try {
      const res = await extractPdf(file);
      setReview(res.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setUploadError(msg || 'PDF extraction failed. Try adding manually.');
    } finally {
      setUploading(false);
    }
  };

  const handleSave = async (data: ProductCreate) => {
    setSaveError('');
    setSaving(true);
    try {
      await createProduct(data);
      setReview(null);
      setShowManual(false);
      load();
    } catch (err: unknown) {
      // Inline error state — no alert() (Issue 23)
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setSaveError(msg || 'Failed to save product. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    setDeleteError('');
    try {
      await deleteProduct(id);
      setProducts((p) => p.filter((x) => x.id !== id));
    } catch {
      setDeleteError('Failed to delete product. Please try again.');
    }
  };

  const handleToggleFavorite = async (product: Product) => {
    const nextFavorite = !product.is_favorite;
    setFavoriteError('');

    // Optimistic update
    setProducts((current) =>
      sortProducts(
        current.map((item) =>
          item.id === product.id ? { ...item, is_favorite: nextFavorite } : item
        )
      )
    );

    try {
      const response = await updateProduct(product.id, { is_favorite: nextFavorite });
      setProducts((current) =>
        sortProducts(
          current.map((item) => (item.id === product.id ? response.data : item))
        )
      );
    } catch {
      // Revert optimistic update and show inline error (Issue 23)
      setProducts((current) =>
        sortProducts(
          current.map((item) =>
            item.id === product.id ? { ...item, is_favorite: product.is_favorite } : item
          )
        )
      );
      setFavoriteError('Failed to update starred product. Please try again.');
    }
  };

  const visibleProducts = products.filter((product) => {
    if (!search.trim()) return true;
    const query = search.toLowerCase();
    return `${product.name} ${product.brand ?? ''}`.toLowerCase().includes(query);
  });

  return (
    <Layout>
      {review && <ReviewModal review={review} onSave={handleSave} onCancel={() => setReview(null)} saving={saving} saveError={saveError} />}
      {showManual && <ManualModal onSave={handleSave} onCancel={() => setShowManual(false)} saving={saving} saveError={saveError} />}
      {selectedProduct && (
        <QuickLogModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onLogged={() => {}}
        />
      )}

      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between animate-fade-up">
          <div>
            <h1 className="text-2xl font-bold text-white">Products</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {products.length > 0 ? `${products.length} product${products.length !== 1 ? 's' : ''} in your library` : 'Build your nutrition library'}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowManual(true)}
              className="btn-secondary text-sm px-4"
            >
              + Manual
            </button>
            <button
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              className="btn-primary text-sm px-4 flex items-center gap-2"
            >
              {uploading ? (
                <>
                  <svg className="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Extracting…
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  Upload PDF
                </>
              )}
            </button>
            <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={handleFileChange} />
          </div>
        </div>

        {products.length > 0 && (
          <div className="animate-fade-up">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search products by name or brand"
              className="input-dark max-w-md"
            />
          </div>
        )}

        {/* General errors */}
        {deleteError && (
          <div role="alert" className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm animate-fade-up flex items-center justify-between">
            <span>{deleteError}</span>
            <button onClick={() => setDeleteError('')} aria-label="Dismiss" className="ml-3 text-red-400 hover:text-red-300">✕</button>
          </div>
        )}
        {favoriteError && (
          <div role="alert" className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm animate-fade-up flex items-center justify-between">
            <span>{favoriteError}</span>
            <button onClick={() => setFavoriteError('')} aria-label="Dismiss" className="ml-3 text-red-400 hover:text-red-300">✕</button>
          </div>
        )}

        {/* Upload error */}
        {uploadError && (
          <div role="alert" className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm animate-fade-up">
            {uploadError}
          </div>
        )}

        {/* Uploading state */}
        {uploading && (
          <div className="glass-card rounded-2xl p-6 text-center animate-fade-up">
            <svg className="animate-spin w-7 h-7 text-brand-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-sm text-gray-300 font-medium">Extracting nutritional data with AI…</p>
            <p className="text-xs text-gray-600 mt-1">This may take a few seconds</p>
          </div>
        )}

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <svg className="animate-spin w-6 h-6 text-brand-500" aria-hidden="true" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : loadError ? (
          /* Load error with retry — users won't confuse this for "No products" (Issue 33) */
          <div role="alert" className="text-center py-16 animate-fade-up">
            <div className="w-14 h-14 glass-card rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl">⚠️</div>
            <p className="text-gray-400 text-sm mb-4">{loadError}</p>
            <button
              onClick={() => { setLoading(true); load(); }}
              className="btn-secondary text-sm"
            >
              Retry
            </button>
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-20 animate-fade-up">
            <div className="w-16 h-16 glass-card rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl">
              📦
            </div>
            <h2 className="text-lg font-semibold text-gray-300 mb-1">No products yet</h2>
            <p className="text-gray-600 text-sm max-w-sm mx-auto">
              Upload a PDF nutrition label and AI will extract macros automatically, or add a product manually.
            </p>
            <div className="flex gap-3 justify-center mt-6">
              <button onClick={() => setShowManual(true)} className="btn-secondary text-sm">
                + Add manually
              </button>
              <button onClick={() => fileRef.current?.click()} className="btn-primary text-sm">
                Upload PDF
              </button>
            </div>
          </div>
        ) : visibleProducts.length === 0 ? (
          <div className="glass-card rounded-2xl p-6 text-sm text-gray-400 animate-fade-up">
            No products match your search.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {visibleProducts.map((p) => (
              <ProductCard
                key={p.id}
                product={p}
                onDelete={handleDelete}
                onSelect={setSelectedProduct}
                onToggleFavorite={handleToggleFavorite}
              />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
