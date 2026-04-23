import api from './client';
import { getBrowserTimezone } from '../utils/timezone';

export interface ParsedItem {
  item: string;
  quantity: number;
  unit: string;
}

export interface CandidateProduct {
  product_id: string;
  name: string;
  brand?: string;
  score: number;
  serving_size_g: number;
  calories_per_serving: number;
}

export interface ParsedItemWithCandidates {
  parsed: ParsedItem;
  candidates: CandidateProduct[];
  needs_confirmation: boolean;
}

export interface ParseResponse {
  items: ParsedItemWithCandidates[];
}

export interface MealItemIn {
  product_id: string;
  quantity: number;
  unit: string;
}

export interface MealItemOut {
  id: string;
  product_id?: string;
  product_name?: string;
  product_brand?: string;
  quantity: number;
  unit: string;
  resolved_nutrients_json?: Record<string, number>;
  confidence_score?: number;
}

export interface ResolvedNutrients {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  sugar_g?: number;
  fiber_g?: number;
  sodium_mg?: number;
}

export interface MealEntryOut {
  id: string;
  user_id: string;
  meal_type: string;
  logged_at: string;
  raw_text: string;
  items: MealItemOut[];
  total_nutrients?: ResolvedNutrients;
}

export interface WeeklyDay {
  date: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  sugar_g?: number;
  fiber_g?: number;
  sodium_mg?: number;
}

export interface MealListParams {
  date_filter?: string;
  search?: string;
  timezone?: string;
  skip?: number;
  limit?: number;
}

export const parseMeal = (raw_text: string) =>
  api.post<ParseResponse>('/meals/parse', { raw_text });

export const createMealEntry = (payload: {
  meal_type: string;
  raw_text: string;
  items: MealItemIn[];
  logged_at?: string;
}) => api.post<MealEntryOut>('/meals', payload);

export const updateMeal = (id: string, payload: {
  meal_type: string;
  raw_text: string;
  items: MealItemIn[];
  logged_at?: string;
}) => api.patch<MealEntryOut>(`/meals/${id}`, payload);

export const listMeals = (params: MealListParams = {}) =>
  api.get<MealEntryOut[]>('/meals', {
    params: { timezone: getBrowserTimezone(), ...params },
  });

export const getTodayMeals = (timezone = getBrowserTimezone()) =>
  api.get<MealEntryOut[]>('/meals/today', { params: { timezone } });

export const getDailyTotals = (dateFilter?: string, timezone = getBrowserTimezone()) =>
  api.get<ResolvedNutrients>('/meals/daily-totals', {
    params: { ...(dateFilter ? { date_filter: dateFilter } : {}), timezone },
  });

export const getWeeklyTotals = (timezone = getBrowserTimezone()) =>
  api.get<WeeklyDay[]>('/meals/weekly-totals', { params: { timezone } });

export const deleteMeal = (id: string) => api.delete(`/meals/${id}`);
