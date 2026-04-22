/**
 * Shared meal/product utility functions.
 *
 * Extracted from LogMealPage and ProductsPage to eliminate duplication (Issue 24).
 */

import type { Product, MealType } from '../types';

/**
 * Suggest a meal type based on the current time of day.
 */
export function getSuggestedMealType(): MealType {
  const h = new Date().getHours();
  if (h < 10) return 'breakfast';
  if (h < 14) return 'lunch';
  if (h < 19) return 'dinner';
  return 'snack';
}

/**
 * Format a serving label for a product.
 * Shows "2 scoops" if serving_quantity and serving_unit are set; otherwise shows "30g".
 */
export function formatServingLabel(product: {
  serving_size_g: number;
  serving_quantity?: number | null;
  serving_unit?: string | null;
}): string {
  if (product.serving_quantity && product.serving_unit) {
    const count = product.serving_quantity;
    const unit =
      count === 1 ? product.serving_unit : `${product.serving_unit}s`;
    return `${count} ${unit}`;
  }
  return `${product.serving_size_g}g`;
}

/**
 * Sort products: favorites first, then by name alphabetically.
 * Consistent behavior across both ProductsPage and LogMealPage (Issue 24).
 */
export function sortProducts(items: Product[]): Product[] {
  return [...items].sort((a, b) => {
    if (a.is_favorite !== b.is_favorite) {
      return a.is_favorite ? -1 : 1;
    }
    return a.name.localeCompare(b.name);
  });
}
