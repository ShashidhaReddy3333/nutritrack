import { useEffect, useState } from 'react';
import { listProducts } from '../api/products';
import { updateMeal } from '../api/meals';
import type { MealEntryOut, MealItemIn } from '../api/meals';
import type { Product, MealType } from '../types';

type EditableMealItem = {
  product_id: string;
  quantity: string;
  unit: string;
};

function formatProductLabel(product: Product) {
  return product.brand ? `${product.name} (${product.brand})` : product.name;
}

export default function MealEditorModal({
  entry,
  onClose,
  onSaved,
}: {
  entry: MealEntryOut;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [mealType, setMealType] = useState<MealType>(entry.meal_type as MealType);
  const [rawText, setRawText] = useState(entry.raw_text);
  const [items, setItems] = useState<EditableMealItem[]>(
    entry.items
      .filter((item) => item.product_id)
      .map((item) => ({
        product_id: item.product_id as string,
        quantity: String(item.quantity),
        unit: item.unit,
      }))
  );

  useEffect(() => {
    listProducts()
      .then((response) => setProducts(response.data))
      .catch(() => setError('Failed to load products'))
      .finally(() => setLoadingProducts(false));
  }, []);

  const handleItemChange = (index: number, field: keyof EditableMealItem, value: string) => {
    setItems((current) => current.map((item, idx) => (
      idx === index ? { ...item, [field]: value } : item
    )));
  };

  const handleSave = async () => {
    const payloadItems: MealItemIn[] = items
      .filter((item) => item.product_id)
      .map((item) => ({
        product_id: item.product_id,
        quantity: parseFloat(item.quantity) || 1,
        unit: item.unit.trim() || 'serving',
      }));

    if (payloadItems.length === 0) {
      setError('Add at least one product to save this meal.');
      return;
    }

    setSaving(true);
    setError('');
    try {
      await updateMeal(entry.id, {
        meal_type: mealType,
        raw_text: rawText,
        logged_at: entry.logged_at,
        items: payloadItems,
      });
      onSaved();
      onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Failed to update meal');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div role="dialog" aria-modal="true" className="bg-dark-800 border border-white/[0.08] rounded-2xl shadow-glass w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-fade-up">
        <div className="p-6 border-b border-white/[0.06]">
          <h2 className="text-lg font-bold text-white">Edit Meal</h2>
          <p className="text-sm text-gray-500 mt-0.5">Update the meal type, text, products, quantity, or unit.</p>
        </div>

        <div className="p-6 space-y-5">
          <div>
            <label className="label-dark">Meal type</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
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

          <div>
            <label className="label-dark">Meal description</label>
            <textarea
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              rows={3}
              className="input-dark resize-none"
            />
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="label-dark mb-0">Meal items</label>
              <button
                type="button"
                onClick={() => setItems((current) => [...current, { product_id: '', quantity: '1', unit: 'serving' }])}
                className="text-sm text-brand-400 hover:text-brand-300 transition-colors"
              >
                + Add item
              </button>
            </div>

            {loadingProducts ? (
              <div className="text-sm text-gray-500">Loading products...</div>
            ) : (
              items.map((item, index) => (
                <div key={`${item.product_id}-${index}`} className="rounded-2xl bg-dark-800/70 border border-white/[0.05] p-4">
                  <div className="grid grid-cols-1 md:grid-cols-[1.4fr_0.5fr_0.6fr_auto] gap-3 items-end">
                    <div>
                      <label className="label-dark">Product</label>
                      <select
                        value={item.product_id}
                        onChange={(e) => handleItemChange(index, 'product_id', e.target.value)}
                        className="input-dark"
                      >
                        <option value="">Select product</option>
                        {products.map((product) => (
                          <option key={product.id} value={product.id}>{formatProductLabel(product)}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="label-dark">Qty</label>
                      <input
                        type="number"
                        min="0.1"
                        step="0.1"
                        value={item.quantity}
                        onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                        className="input-dark"
                      />
                    </div>
                    <div>
                      <label className="label-dark">Unit</label>
                      <input
                        value={item.unit}
                        onChange={(e) => handleItemChange(index, 'unit', e.target.value)}
                        className="input-dark"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => setItems((current) => current.filter((_item, idx) => idx !== index))}
                      className="btn-secondary"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {error && (
            <div className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm">
              {error}
            </div>
          )}
        </div>

        <div className="p-6 border-t border-white/[0.06] flex gap-3">
          <button onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          <button onClick={handleSave} disabled={saving} className="btn-primary flex-1">
            {saving ? 'Saving...' : 'Save changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
