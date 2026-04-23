import api from './client';
import type { Product } from '../types';

export interface NutrientData {
  serving_size_g: number;
  serving_quantity?: number;
  serving_unit?: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  sugar_g?: number;
  fiber_g?: number;
  sodium_mg?: number;
  other_nutrients?: Record<string, unknown>;
}

export interface ExtractionReview {
  extracted: NutrientData;
  raw_text_snippet: string;
  confidence: 'high' | 'medium' | 'low';
  suggested_name?: string;
  suggested_brand?: string;
}

export interface ProductCreate {
  name: string;
  brand?: string | null;
  serving_size_g: number;
  serving_quantity?: number | null;
  serving_unit?: string | null;
  is_favorite?: boolean;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  sugar_g?: number | null;
  fiber_g?: number | null;
  sodium_mg?: number | null;
  other_nutrients_json?: Record<string, unknown> | null;
}

export interface ProductListParams {
  skip?: number;
  limit?: number;
  search?: string;
}

export const extractPdf = (file: File) => {
  const form = new FormData();
  form.append('file', file);
  return api.post<ExtractionReview>('/products/extract', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const createProduct = (data: ProductCreate) =>
  api.post<Product>('/products', data);

export const listProducts = (params: ProductListParams = {}) =>
  api.get<Product[]>('/products', { params });

export const listAllProducts = async (search?: string, max = 5000) => {
  const limit = 200;
  const products: Product[] = [];
  for (let skip = 0; skip < max; skip += limit) {
    const response = await listProducts({ skip, limit, search });
    products.push(...response.data);
    if (response.data.length < limit) break;
  }
  return products;
};

export const deleteProduct = (id: string) => api.delete(`/products/${id}`);

export const updateProduct = (id: string, data: Partial<ProductCreate>) =>
  api.patch<Product>(`/products/${id}`, data);
