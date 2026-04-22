// ── Auth ──────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserOut {
  id: string;
  email: string;
  created_at: string;
}

// ── Profile ───────────────────────────────────────────────────────────────────

export type Sex = 'male' | 'female' | 'other';
export type ActivityLevel =
  | 'sedentary'
  | 'lightly_active'
  | 'moderately_active'
  | 'very_active'
  | 'extra_active';
export type Goal = 'maintain' | 'cut' | 'bulk';

export interface DailyTargets {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  sugar_g?: number;
  fiber_g?: number;
  sodium_mg?: number;
}

export interface BodyCompositionReport {
  bwi_result?: string;
  bio_age?: string;
  waist_to_hip_ratio?: string;
  summary: Record<string, string>;
  body_composition: Record<string, string>;
  segmental_analysis: Record<string, string>;
}

export interface ProfileOut {
  id: string;
  user_id: string;
  age: number;
  sex: Sex;
  weight_kg: number;
  height_cm: number;
  activity_level: ActivityLevel;
  goal: Goal;
  daily_targets_json?: DailyTargets;
  calculated_targets?: DailyTargets;
  body_composition_json?: BodyCompositionReport;
}

export interface ProfileCreate {
  age: number;
  sex: Sex;
  weight_kg: number;
  height_cm: number;
  activity_level: ActivityLevel;
  goal: Goal;
  override_targets?: DailyTargets | null;
  body_composition_report?: BodyCompositionReport;
}

export interface ProfileUpdate extends Partial<ProfileCreate> {}

// ── Products (stub — Phase 2) ─────────────────────────────────────────────────

export interface Product {
  id: string;
  user_id: string;
  name: string;
  brand?: string;
  serving_size_g: number;
  serving_quantity?: number;
  serving_unit?: string;
  is_favorite: boolean;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  sugar_g?: number;
  fiber_g?: number;
  sodium_mg?: number;
  created_at: string;
}

// ── Meals (stub — Phase 3) ────────────────────────────────────────────────────

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';
