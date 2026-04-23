export interface UserOut {
  id: string;
  email: string;
  created_at: string;
}

export interface SessionResponse {
  authenticated: boolean;
  user: UserOut;
}

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
  sugar_g?: number | null;
  fiber_g?: number | null;
  sodium_mg?: number | null;
}

export interface BodyCompositionReport {
  bwi_result?: string | null;
  bio_age?: string | null;
  waist_to_hip_ratio?: string | null;
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
  timezone: string;
  daily_targets_json?: DailyTargets | null;
  calculated_targets?: DailyTargets | null;
  body_composition_json?: BodyCompositionReport | null;
}

export interface ProfileCreate {
  age: number;
  sex: Sex;
  weight_kg: number;
  height_cm: number;
  activity_level: ActivityLevel;
  goal: Goal;
  timezone: string;
  override_targets?: DailyTargets | null;
  body_composition_report?: BodyCompositionReport | null;
}

export interface ProfileUpdate extends Partial<ProfileCreate> {}

export interface Product {
  id: string;
  user_id: string;
  name: string;
  brand?: string | null;
  serving_size_g: number;
  serving_quantity?: number | null;
  serving_unit?: string | null;
  is_favorite: boolean;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  sugar_g?: number | null;
  fiber_g?: number | null;
  sodium_mg?: number | null;
  created_at: string;
  has_source_pdf?: boolean;
  chroma_indexed?: boolean;
}

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';
