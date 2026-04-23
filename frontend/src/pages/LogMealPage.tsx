import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { parseMeal, createMealEntry } from '../api/meals';
import type { ParsedItemWithCandidates, MealItemIn } from '../api/meals';
import { listAllProducts } from '../api/products';
import type { Product, MealType } from '../types';
import { formatServingLabel, getSuggestedMealType, sortProducts } from '../utils/mealUtils';

const MEAL_ICONS: Record<MealType, string> = {
  breakfast: 'Sunrise',
  lunch: 'Sun',
  dinner: 'Moon',
  snack: 'Apple',
};

type ManualMealItem = {
  product: Product;
  quantity: string;
  unit: string;
};

function ItemRow({
  item,
  index,
  onSelectProduct,
  onUpdateQuantity,
  onUpdateUnit,
  selectedProductId,
}: {
  item: ParsedItemWithCandidates;
  index: number;
  onSelectProduct: (idx: number, productId: string) => void;
  onUpdateQuantity: (idx: number, q: number) => void;
  onUpdateUnit: (idx: number, u: string) => void;
  selectedProductId: string | null;
}) {
  const isConfirmed = !!selectedProductId;
  const selected = item.candidates.find((c) => c.product_id === selectedProductId);

  return (
    <div className={`glass-card rounded-2xl p-5 border-l-4 transition-all duration-300 animate-fade-up ${
      isConfirmed
        ? 'border-l-brand-500'
        : item.needs_confirmation
        ? 'border-l-accent-yellow'
        : 'border-l-dark-600'
    }`}>
      <div className="flex items-start gap-3 mb-4">
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
          isConfirmed ? 'bg-brand-500/20' : 'bg-accent-yellow-dim'
        }`}>
          {isConfirmed ? (
            <svg className="w-4 h-4 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg className="w-4 h-4 text-accent-yellow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-gray-100 text-sm">{item.parsed.item}</div>
          <div className={`text-xs mt-0.5 ${isConfirmed ? 'text-brand-400' : 'text-accent-yellow'}`}>
            {isConfirmed ? `Matched: ${selected?.name}` : 'Select a product to confirm'}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <input
            type="number"
            min="0.1"
            step="0.1"
            value={item.parsed.quantity}
            onChange={(e) => onUpdateQuantity(index, parseFloat(e.target.value) || 1)}
            className="w-16 bg-dark-700 border border-dark-600 text-gray-100 rounded-lg px-2 py-1.5 text-sm text-center focus:outline-none focus:ring-1 focus:ring-brand-500/50"
          />
          <input
            value={item.parsed.unit}
            onChange={(e) => onUpdateUnit(index, e.target.value)}
            className="w-20 bg-dark-700 border border-dark-600 text-gray-100 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500/50"
            placeholder="unit"
          />
        </div>
      </div>

      {item.candidates.length === 0 ? (
        <div className="text-xs text-gray-600 italic py-1 pl-11">No matching products found in your library.</div>
      ) : (
        <div className="space-y-1.5 pl-11">
          {item.candidates.map((c) => (
            <button
              key={c.product_id}
              onClick={() => onSelectProduct(index, c.product_id)}
              className={`w-full flex items-center justify-between text-left px-3 py-2.5 rounded-xl text-sm transition-all duration-150 ${
                selectedProductId === c.product_id
                  ? 'bg-brand-500/15 border border-brand-500/40 shadow-glow-brand'
                  : 'bg-dark-700/60 border border-white/[0.05] hover:border-white/[0.12] hover:bg-dark-700'
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                {selectedProductId === c.product_id && (
                  <svg className="w-3.5 h-3.5 text-brand-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                )}
                <span className={`font-medium truncate ${selectedProductId === c.product_id ? 'text-brand-300' : 'text-gray-200'}`}>{c.name}</span>
                {c.brand && <span className="text-gray-500 text-xs ml-1 flex-shrink-0">· {c.brand}</span>}
              </div>
              <div className="text-xs text-right flex-shrink-0 ml-3">
                <div className="text-gray-400">{Math.round(c.calories_per_serving)} kcal</div>
                <div className={`font-medium ${c.score > 0.8 ? 'text-brand-400' : c.score > 0.6 ? 'text-accent-yellow' : 'text-gray-500'}`}>
                  {Math.round(c.score * 100)}% match
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function ManualProductRow({
  item,
  index,
  onUpdateQuantity,
  onUpdateUnit,
  onRemove,
}: {
  item: ManualMealItem;
  index: number;
  onUpdateQuantity: (index: number, value: string) => void;
  onUpdateUnit: (index: number, value: string) => void;
  onRemove: (index: number) => void;
}) {
  return (
    <div className="glass-card rounded-2xl p-4 animate-fade-up">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold text-gray-100">{item.product.name}</div>
          <div className="text-xs text-gray-500 mt-1">
            {item.product.brand ? `${item.product.brand} · ` : ''}
            {Math.round(item.product.calories)} kcal per {formatServingLabel(item.product)}
          </div>
        </div>
        <button
          type="button"
          onClick={() => onRemove(index)}
          className="text-xs text-gray-500 hover:text-red-400 transition-colors"
        >
          Remove
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3 mt-4">
        <div>
          <label className="label-dark">Quantity</label>
          <input
            type="number"
            min="0.1"
            step="0.1"
            value={item.quantity}
            onChange={(e) => onUpdateQuantity(index, e.target.value)}
            className="input-dark"
          />
        </div>
        <div>
          <label className="label-dark">Unit</label>
          <input
            value={item.unit}
            onChange={(e) => onUpdateUnit(index, e.target.value)}
            className="input-dark"
            placeholder="serving"
          />
        </div>
      </div>
    </div>
  );
}

export default function LogMealPage() {
  const navigate = useNavigate();
  const [mealType, setMealType] = useState<MealType>(getSuggestedMealType);
  const [rawText, setRawText] = useState('');
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState('');
  const [parsedItems, setParsedItems] = useState<ParsedItemWithCandidates[] | null>(null);
  const [quantities, setQuantities] = useState<number[]>([]);
  const [units, setUnits] = useState<string[]>([]);
  const [selections, setSelections] = useState<(string | null)[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [productsLoading, setProductsLoading] = useState(true);
  const [productSearch, setProductSearch] = useState('');
  const [manualItems, setManualItems] = useState<ManualMealItem[]>([]);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');

  useEffect(() => {
    listAllProducts()
      .then((data) => setProducts(sortProducts(data)))
      .catch(() => {})
      .finally(() => setProductsLoading(false));
  }, []);

  const filteredProducts = sortProducts(
    products.filter((product) => {
      if (!productSearch.trim()) return false;
      const query = productSearch.toLowerCase();
      const text = `${product.name} ${product.brand ?? ''}`.toLowerCase();
      const alreadyAdded = manualItems.some((item) => item.product.id === product.id);
      return text.includes(query) && !alreadyAdded;
    })
  ).slice(0, 8);

  const handleParse = async () => {
    if (!rawText.trim()) return;
    setParsing(true);
    setParseError('');
    setParsedItems(null);
    try {
      const res = await parseMeal(rawText);
      const items = res.data.items;
      setParsedItems(items);
      setQuantities(items.map((i) => i.parsed.quantity));
      setUnits(items.map((i) => i.parsed.unit));
      setSelections(
        items.map((i) =>
          !i.needs_confirmation && i.candidates[0] ? i.candidates[0].product_id : null
        )
      );
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setParseError(msg || 'Parsing failed. Check your AI setup or try again.');
    } finally {
      setParsing(false);
    }
  };

  const handleLogParsedMeal = async () => {
    if (!parsedItems) return;
    const items: MealItemIn[] = parsedItems
      .map((_item, i) => ({
        product_id: selections[i] ?? '',
        quantity: quantities[i],
        unit: units[i],
      }))
      .filter((item) => item.product_id);

    if (items.length === 0) {
      setSaveError('Please select at least one product match before logging.');
      return;
    }

    setSaving(true);
    setSaveError('');
    try {
      await createMealEntry({ meal_type: mealType, raw_text: rawText, items });
      navigate('/dashboard');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setSaveError(msg || 'Failed to log meal');
    } finally {
      setSaving(false);
    }
  };

  const handleAddManualProduct = (product: Product) => {
    setManualItems((current) => [
      ...current,
      {
        product,
        quantity: product.serving_quantity ? String(product.serving_quantity) : '1',
        unit: product.serving_unit || 'serving',
      },
    ]);
    setProductSearch('');
    setSaveError('');
  };

  const handleLogManualMeal = async () => {
    if (manualItems.length === 0) {
      setSaveError('Add at least one saved product before logging.');
      return;
    }

    const items: MealItemIn[] = manualItems.map((item) => ({
      product_id: item.product.id,
      quantity: parseFloat(item.quantity) || 1,
      unit: item.unit.trim() || 'serving',
    }));

    const rawTextSummary = manualItems
      .map((item) => `${item.quantity || '1'} ${item.unit || 'serving'} ${item.product.name}`)
      .join(', ');

    setSaving(true);
    setSaveError('');
    try {
      await createMealEntry({
        meal_type: mealType,
        raw_text: rawTextSummary,
        items,
      });
      navigate('/dashboard');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setSaveError(msg || 'Failed to log meal');
    } finally {
      setSaving(false);
    }
  };

  const resolvedCount = selections.filter(Boolean).length;

  return (
    <Layout>
      <div className="max-w-3xl mx-auto space-y-5">
        <div className="animate-fade-up">
          <h1 className="text-2xl font-bold text-white">Log a Meal</h1>
          <p className="text-sm text-gray-500 mt-0.5">Search saved products directly or describe the meal for AI matching.</p>
        </div>

        <div className="glass-card rounded-2xl p-6 space-y-5 animate-fade-up">
          <div>
            <label className="label-dark">Meal type</label>
            <div className="flex gap-2 flex-wrap">
              {(['breakfast', 'lunch', 'dinner', 'snack'] as MealType[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setMealType(t)}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                    mealType === t
                      ? 'bg-brand-500/20 text-brand-400 border border-brand-500/40'
                      : 'bg-dark-700 text-gray-400 border border-transparent hover:text-gray-200 hover:border-white/[0.08]'
                  }`}
                >
                  {MEAL_ICONS[t]} {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_0.8fr] gap-5">
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="label-dark">Quick add from your products</label>
                  <span className="text-xs text-gray-600">{manualItems.length} selected</span>
                </div>
                <input
                  value={productSearch}
                  onChange={(e) => setProductSearch(e.target.value)}
                  placeholder="Search saved products by name or brand"
                  className="input-dark"
                />
              </div>

              {productsLoading ? (
                <div className="text-sm text-gray-500">Loading your products...</div>
              ) : products.length === 0 ? (
                <div className="bg-dark-700/40 border border-white/[0.06] rounded-xl p-4 text-sm text-gray-400">
                  No saved products yet.
                  <button onClick={() => navigate('/products')} className="ml-2 text-brand-400 hover:text-brand-300">
                    Add products
                  </button>
                </div>
              ) : productSearch.trim() && filteredProducts.length === 0 ? (
                <div className="bg-dark-700/40 border border-white/[0.06] rounded-xl p-4 text-sm text-gray-500">
                  No matching products found.
                </div>
              ) : filteredProducts.length > 0 ? (
                <div className="space-y-2">
                  {filteredProducts.map((product) => (
                    <button
                      key={product.id}
                      type="button"
                      onClick={() => handleAddManualProduct(product)}
                      className="w-full text-left glass-card-hover rounded-2xl p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="min-w-0">
                          <div className="text-sm font-semibold text-gray-100 truncate">{product.name}</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {product.brand ? `${product.brand} · ` : ''}
                            {Math.round(product.calories)} kcal per {formatServingLabel(product)}
                          </div>
                        </div>
                        <span className="text-xs text-brand-400">Add</span>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="bg-dark-700/40 border border-white/[0.06] rounded-xl p-4 text-sm text-gray-500">
                  Start typing to search your saved products.
                </div>
              )}

              {manualItems.length > 0 && (
                <div className="space-y-3">
                  {manualItems.map((item, index) => (
                    <ManualProductRow
                      key={`${item.product.id}-${index}`}
                      item={item}
                      index={index}
                      onUpdateQuantity={(itemIndex, value) => setManualItems((current) => current.map((entry, idx) => (
                        idx === itemIndex ? { ...entry, quantity: value } : entry
                      )))}
                      onUpdateUnit={(itemIndex, value) => setManualItems((current) => current.map((entry, idx) => (
                        idx === itemIndex ? { ...entry, unit: value } : entry
                      )))}
                      onRemove={(itemIndex) => setManualItems((current) => current.filter((_entry, idx) => idx !== itemIndex))}
                    />
                  ))}
                </div>
              )}

              {manualItems.length > 0 && (
                <button
                  onClick={handleLogManualMeal}
                  disabled={saving}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  {saving ? 'Logging...' : `Log ${manualItems.length} saved product${manualItems.length !== 1 ? 's' : ''}`}
                </button>
              )}
            </div>

            <div className="space-y-4">
              <div className="rounded-2xl border border-white/[0.06] bg-dark-800/60 p-5 space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="label-dark">Describe the meal for AI matching</label>
                    <span className="text-xs text-gray-600">{rawText.length} chars</span>
                  </div>
                  <textarea
                    value={rawText}
                    onChange={(e) => setRawText(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleParse(); } }}
                    placeholder="e.g. 2 eggs, 2 slices bread, 1 cup oats"
                    rows={6}
                    className="w-full bg-dark-700 border border-dark-600 text-gray-100 rounded-xl px-4 py-3 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500/40 resize-none transition-all text-sm"
                  />
                </div>

                <button
                  onClick={handleParse}
                  disabled={parsing || !rawText.trim()}
                  className="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  {parsing ? 'Parsing...' : 'Parse and match'}
                </button>

                {parseError && (
                  <div className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm">
                    {parseError}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {parsedItems && (
          <>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-white">Confirm AI Matches</h2>
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                  resolvedCount === parsedItems.length
                    ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                    : 'bg-white/[0.05] text-gray-500 border border-white/[0.08]'
                }`}>
                  {resolvedCount} / {parsedItems.length} matched
                </span>
              </div>
              {parsedItems.map((item, i) => (
                <ItemRow
                  key={i}
                  index={i}
                  item={{ ...item, parsed: { ...item.parsed, quantity: quantities[i], unit: units[i] } }}
                  selectedProductId={selections[i]}
                  onSelectProduct={(idx, pid) => setSelections((s) => { const next = [...s]; next[idx] = pid; return next; })}
                  onUpdateQuantity={(idx, q) => setQuantities((qs) => { const next = [...qs]; next[idx] = q; return next; })}
                  onUpdateUnit={(idx, u) => setUnits((us) => { const next = [...us]; next[idx] = u; return next; })}
                />
              ))}
            </div>

            {saveError && (
              <div className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm">
                {saveError}
              </div>
            )}

            <div className="flex gap-3 sticky bottom-4">
              <button
                onClick={() => { setParsedItems(null); setRawText(''); }}
                className="btn-secondary flex-1"
              >
                Clear
              </button>
              <button
                onClick={handleLogParsedMeal}
                disabled={saving || resolvedCount === 0}
                className="btn-primary flex-[2] flex items-center justify-center gap-2"
              >
                {saving ? 'Logging...' : `Log ${resolvedCount} AI-matched item${resolvedCount !== 1 ? 's' : ''}`}
              </button>
            </div>
          </>
        )}

        {saveError && !parsedItems && (
          <div className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm">
            {saveError}
          </div>
        )}
      </div>
    </Layout>
  );
}
