import { useEffect, useState } from 'react';
import { getProfile, updateProfile } from '../api/profile';
import type { ActivityLevel, BodyCompositionReport, DailyTargets, Goal, ProfileOut } from '../types';
import Layout from '../components/Layout';
import {
  BODY_COMPOSITION_FIELDS,
  parseBodyCompositionReport,
  SEGMENTAL_FIELDS,
  SUMMARY_FIELDS,
  TOP_LEVEL_FIELDS,
} from '../utils/bodyComposition';

const ACTIVITY_LABELS: Record<ActivityLevel, string> = {
  sedentary: 'Sedentary',
  lightly_active: 'Lightly active',
  moderately_active: 'Moderately active',
  very_active: 'Very active',
  extra_active: 'Extra active',
};

const GOAL_LABELS: Record<Goal, string> = {
  maintain: 'Maintain weight',
  cut: 'Lose weight',
  bulk: 'Gain muscle',
};

const GOAL_ICONS: Record<Goal, string> = {
  maintain: '⚖️',
  cut: '🔥',
  bulk: '💪',
};

type TargetFormState = {
  calories: string;
  protein_g: string;
  carbs_g: string;
  fat_g: string;
  fiber_g: string;
  sugar_g: string;
  sodium_mg: string;
};

const EMPTY_TARGETS: TargetFormState = {
  calories: '',
  protein_g: '',
  carbs_g: '',
  fat_g: '',
  fiber_g: '',
  sugar_g: '',
  sodium_mg: '',
};

function buildTargetState(targets?: DailyTargets): TargetFormState {
  if (!targets) return EMPTY_TARGETS;

  return {
    calories: String(targets.calories ?? ''),
    protein_g: String(targets.protein_g ?? ''),
    carbs_g: String(targets.carbs_g ?? ''),
    fat_g: String(targets.fat_g ?? ''),
    fiber_g: targets.fiber_g != null ? String(targets.fiber_g) : '',
    sugar_g: targets.sugar_g != null ? String(targets.sugar_g) : '',
    sodium_mg: targets.sodium_mg != null ? String(targets.sodium_mg) : '',
  };
}

function parseOptionalNumber(value: string) {
  if (!value.trim()) return undefined;
  return parseFloat(value);
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="glass-card rounded-2xl p-4 text-center animate-fade-up">
      <div className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-2">{label}</div>
      <div className="text-2xl font-bold text-white tabular-nums">{value}</div>
      {sub && <div className="text-xs text-gray-600 mt-0.5">{sub}</div>}
    </div>
  );
}

function TargetRow({ label, value, unit, colorClass }: { label: string; value: number; unit: string; colorClass: string }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-white/[0.05] last:border-0">
      <span className="text-sm text-gray-400">{label}</span>
      <span className={`text-sm font-semibold tabular-nums ${colorClass}`}>
        {Math.round(value)} <span className="text-xs font-normal text-gray-600">{unit}</span>
      </span>
    </div>
  );
}

function MetricGrid({
  title,
  report,
  fields,
  source,
}: {
  title: string;
  report: BodyCompositionReport;
  fields: Array<{ key: string; label: string }>;
  source: 'summary' | 'body_composition' | 'segmental_analysis';
}) {
  const values = report[source];
  const visibleFields = fields.filter((field) => values[field.key]);

  if (visibleFields.length === 0) return null;

  return (
    <div className="glass-card rounded-2xl p-5 animate-fade-up">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">{title}</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {visibleFields.map((field) => (
          <div key={field.key} className="bg-dark-700/60 rounded-xl p-4">
            <div className="text-xs text-gray-600 mb-1">{field.label}</div>
            <div className="text-sm font-semibold text-gray-200">{values[field.key]}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [weight, setWeight] = useState('');
  const [height, setHeight] = useState('');
  const [age, setAge] = useState('');
  const [goal, setGoal] = useState<Goal>('maintain');
  const [activity, setActivity] = useState<ActivityLevel>('moderately_active');
  const [bodyReport, setBodyReport] = useState<BodyCompositionReport | null>(null);
  const [useCustomTargets, setUseCustomTargets] = useState(false);
  const [targetValues, setTargetValues] = useState<TargetFormState>(EMPTY_TARGETS);
  const [scanText, setScanText] = useState('');
  const [scanError, setScanError] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');

  useEffect(() => {
    getProfile()
      .then((r) => {
        setProfile(r.data);
        setWeight(String(r.data.weight_kg));
        setHeight(String(r.data.height_cm));
        setAge(String(r.data.age));
        setGoal(r.data.goal);
        setActivity(r.data.activity_level);
        setBodyReport(r.data.body_composition_json ?? null);
        setUseCustomTargets(Boolean(r.data.daily_targets_json));
        setTargetValues(buildTargetState(r.data.daily_targets_json ?? r.data.calculated_targets));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleImportScan = () => {
    const parsed = parseBodyCompositionReport(scanText);
    if (!parsed) {
    setScanError('Could not parse the pasted report. Include labeled rows such as Body Fat %, Fat Mass, Muscle Mass, and Total Body Water, or enter the values manually.');
      return;
    }
    setBodyReport(parsed);
    setScanError('');
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError('');
    try {
      const overrideTargets = useCustomTargets
        ? {
            calories: parseFloat(targetValues.calories) || 0,
            protein_g: parseFloat(targetValues.protein_g) || 0,
            carbs_g: parseFloat(targetValues.carbs_g) || 0,
            fat_g: parseFloat(targetValues.fat_g) || 0,
            fiber_g: parseOptionalNumber(targetValues.fiber_g),
            sugar_g: parseOptionalNumber(targetValues.sugar_g),
            sodium_mg: parseOptionalNumber(targetValues.sodium_mg),
          }
        : null;

      const r = await updateProfile({
        age: parseInt(age),
        weight_kg: parseFloat(weight),
        height_cm: parseFloat(height),
        goal,
        activity_level: activity,
        override_targets: overrideTargets,
        body_composition_report: bodyReport ?? undefined,
      });
      setProfile(r.data);
      setBodyReport(r.data.body_composition_json ?? null);
      setUseCustomTargets(Boolean(r.data.daily_targets_json));
      setTargetValues(buildTargetState(r.data.daily_targets_json ?? r.data.calculated_targets));
      setEditing(false);
      setScanError('');
    } catch {
      setSaveError('Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <svg className="animate-spin w-7 h-7 text-brand-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      </Layout>
    );
  }

  if (!profile) {
    return (
      <Layout>
        <div className="text-center py-20 text-gray-500">No profile found.</div>
      </Layout>
    );
  }

  const targets = profile.daily_targets_json ?? profile.calculated_targets;
  const topLevelMetrics = TOP_LEVEL_FIELDS.filter((field) => bodyReport?.[field.key as keyof BodyCompositionReport]);

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-5">
        <div className="flex items-center justify-between animate-fade-up">
          <div>
            <h1 className="text-2xl font-bold text-white">My Profile</h1>
            <p className="text-sm text-gray-500 mt-0.5">Your body stats, scan results, and nutrition goals</p>
          </div>
          {!editing && (
            <button onClick={() => setEditing(true)} className="btn-secondary text-sm px-4 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit
            </button>
          )}
        </div>

        {!editing ? (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <StatCard label="Age" value={profile.age} sub="years" />
              <StatCard label="Weight" value={profile.weight_kg} sub="kg" />
              <StatCard label="Height" value={profile.height_cm} sub="cm" />
              <StatCard label="Sex" value={profile.sex.charAt(0).toUpperCase() + profile.sex.slice(1)} />
            </div>

            <div className="glass-card rounded-2xl p-5 animate-fade-up">
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Settings</h2>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-dark-700/60 rounded-xl p-4">
                  <div className="text-xs text-gray-600 mb-1">Activity level</div>
                  <div className="text-sm font-semibold text-gray-200">{ACTIVITY_LABELS[profile.activity_level]}</div>
                </div>
                <div className="bg-dark-700/60 rounded-xl p-4">
                  <div className="text-xs text-gray-600 mb-1">Goal</div>
                  <div className="text-sm font-semibold text-gray-200 flex items-center gap-1.5">
                    <span>{GOAL_ICONS[profile.goal]}</span>
                    {GOAL_LABELS[profile.goal]}
                  </div>
                </div>
              </div>
            </div>

            {targets && (
              <div className="glass-card rounded-2xl p-5 animate-fade-up">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Daily Targets</h2>
                  {profile.daily_targets_json && (
                    <span className="text-xs bg-accent-yellow-dim text-accent-yellow px-2 py-0.5 rounded-full border border-accent-yellow/30">
                      Custom override
                    </span>
                  )}
                </div>
                <TargetRow label="Calories" value={targets.calories} unit="kcal" colorClass="text-accent-orange" />
                <TargetRow label="Protein" value={targets.protein_g} unit="g" colorClass="text-accent-blue" />
                <TargetRow label="Carbohydrates" value={targets.carbs_g} unit="g" colorClass="text-accent-yellow" />
                <TargetRow label="Fat" value={targets.fat_g} unit="g" colorClass="text-accent-purple" />
                {targets.fiber_g && <TargetRow label="Fiber" value={targets.fiber_g} unit="g" colorClass="text-brand-400" />}
                {targets.sodium_mg && <TargetRow label="Sodium" value={targets.sodium_mg} unit="mg" colorClass="text-gray-400" />}
                {targets.sugar_g && <TargetRow label="Sugar (limit)" value={targets.sugar_g} unit="g" colorClass="text-accent-pink" />}
              </div>
            )}

            {bodyReport && (
              <>
                <div className="glass-card rounded-2xl p-5 animate-fade-up">
                  <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Body Scan Snapshot</h2>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {topLevelMetrics.map((field) => (
                      <div key={field.key} className="bg-dark-700/60 rounded-xl p-4">
                        <div className="text-xs text-gray-600 mb-1">{field.label}</div>
                        <div className="text-sm font-semibold text-gray-200">
                          {bodyReport[field.key as keyof BodyCompositionReport] as string}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <MetricGrid title="Summary" report={bodyReport} fields={SUMMARY_FIELDS} source="summary" />
                <MetricGrid title="Body Composition" report={bodyReport} fields={BODY_COMPOSITION_FIELDS} source="body_composition" />
                <MetricGrid title="Segmental Analysis" report={bodyReport} fields={SEGMENTAL_FIELDS} source="segmental_analysis" />
              </>
            )}
          </>
        ) : (
          <div className="glass-card rounded-2xl p-6 space-y-5 animate-fade-up">
            <h2 className="font-semibold text-white">Edit Profile</h2>

            {saveError && (
              <div role="alert" className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm">
                {saveError}
              </div>
            )}

            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Body stats</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label-dark">Age</label>
                  <input type="number" value={age} onChange={(e) => setAge(e.target.value)} className="input-dark" placeholder="28" />
                </div>
                <div>
                  <label className="label-dark">Weight (kg)</label>
                  <input type="number" step={0.1} value={weight} onChange={(e) => setWeight(e.target.value)} className="input-dark" placeholder="75" />
                </div>
                <div className="col-span-2">
                  <label className="label-dark">Height (cm)</label>
                  <input type="number" value={height} onChange={(e) => setHeight(e.target.value)} className="input-dark" placeholder="175" />
                </div>
              </div>
            </div>

            <div>
              <label className="label-dark">Goal</label>
              <select value={goal} onChange={(e) => setGoal(e.target.value as Goal)} className="input-dark">
                <option value="maintain">Maintain weight</option>
                <option value="cut">Lose weight</option>
                <option value="bulk">Gain muscle</option>
              </select>
            </div>

            <div>
              <label className="label-dark">Activity Level</label>
              <select value={activity} onChange={(e) => setActivity(e.target.value as ActivityLevel)} className="input-dark">
                <option value="sedentary">Sedentary</option>
                <option value="lightly_active">Lightly active</option>
                <option value="moderately_active">Moderately active</option>
                <option value="very_active">Very active</option>
                <option value="extra_active">Extra active</option>
              </select>
            </div>

            <div className="space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Daily target override</p>
                  <p className="text-sm text-gray-500 mt-1">
                    Set your own calories and macros, or use the calculated targets from your profile.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setUseCustomTargets((current) => {
                      const next = !current;
                      if (!current) {
                        setTargetValues(buildTargetState(profile.daily_targets_json ?? profile.calculated_targets));
                      }
                      return next;
                    });
                  }}
                  className={`rounded-xl px-3 py-2 text-sm font-medium transition-all ${
                    useCustomTargets
                      ? 'bg-accent-yellow-dim text-accent-yellow border border-accent-yellow/30'
                      : 'bg-dark-700 text-gray-400 border border-white/[0.08]'
                  }`}
                >
                  {useCustomTargets ? 'Using custom targets' : 'Use calculated targets'}
                </button>
              </div>

              {useCustomTargets ? (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label-dark">Calories (kcal)</label>
                    <input
                      type="number"
                      value={targetValues.calories}
                      onChange={(e) => setTargetValues((current) => ({ ...current, calories: e.target.value }))}
                      className="input-dark"
                    />
                  </div>
                  <div>
                    <label className="label-dark">Protein (g)</label>
                    <input
                      type="number"
                      value={targetValues.protein_g}
                      onChange={(e) => setTargetValues((current) => ({ ...current, protein_g: e.target.value }))}
                      className="input-dark"
                    />
                  </div>
                  <div>
                    <label className="label-dark">Carbs (g)</label>
                    <input
                      type="number"
                      value={targetValues.carbs_g}
                      onChange={(e) => setTargetValues((current) => ({ ...current, carbs_g: e.target.value }))}
                      className="input-dark"
                    />
                  </div>
                  <div>
                    <label className="label-dark">Fat (g)</label>
                    <input
                      type="number"
                      value={targetValues.fat_g}
                      onChange={(e) => setTargetValues((current) => ({ ...current, fat_g: e.target.value }))}
                      className="input-dark"
                    />
                  </div>
                  <div>
                    <label className="label-dark">Fiber (g)</label>
                    <input
                      type="number"
                      value={targetValues.fiber_g}
                      onChange={(e) => setTargetValues((current) => ({ ...current, fiber_g: e.target.value }))}
                      className="input-dark"
                    />
                  </div>
                  <div>
                    <label className="label-dark">Sugar limit (g)</label>
                    <input
                      type="number"
                      value={targetValues.sugar_g}
                      onChange={(e) => setTargetValues((current) => ({ ...current, sugar_g: e.target.value }))}
                      className="input-dark"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="label-dark">Sodium (mg)</label>
                    <input
                      type="number"
                      value={targetValues.sodium_mg}
                      onChange={(e) => setTargetValues((current) => ({ ...current, sodium_mg: e.target.value }))}
                      className="input-dark"
                    />
                  </div>
                </div>
              ) : (
                <div className="glass-card rounded-2xl p-4">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="text-gray-500">Calories</div>
                    <div className="text-right text-gray-200">{Math.round((profile.calculated_targets ?? profile.daily_targets_json)?.calories ?? 0)} kcal</div>
                    <div className="text-gray-500">Protein</div>
                    <div className="text-right text-gray-200">{Math.round((profile.calculated_targets ?? profile.daily_targets_json)?.protein_g ?? 0)} g</div>
                    <div className="text-gray-500">Carbs</div>
                    <div className="text-right text-gray-200">{Math.round((profile.calculated_targets ?? profile.daily_targets_json)?.carbs_g ?? 0)} g</div>
                    <div className="text-gray-500">Fat</div>
                    <div className="text-right text-gray-200">{Math.round((profile.calculated_targets ?? profile.daily_targets_json)?.fat_g ?? 0)} g</div>
                  </div>
                </div>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="label-dark">Body composition report</label>
                {bodyReport && <span className="text-xs text-brand-400">Imported and ready to save</span>}
              </div>
              <textarea
                value={scanText}
                onChange={(e) => setScanText(e.target.value)}
                rows={12}
                className="w-full bg-dark-700 border border-dark-600 text-gray-100 rounded-xl px-4 py-3 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500/40 resize-y transition-all text-sm"
                placeholder="Paste a body scan report here, for example BWI RESULT, SUMMARY, BODY COMPOSITION, and SEGMENTAL ANALYSIS values."
              />
              <div className="flex items-center justify-between mt-3">
                {scanError ? <span role="alert" className="text-xs text-red-400">{scanError}</span> : <span className="text-xs text-gray-500">Paste the scan text, then import it before saving.</span>}
                <button type="button" onClick={handleImportScan} className="btn-secondary text-sm px-4">
                  Import scan
                </button>
              </div>
            </div>

            <div className="flex gap-3 pt-1">
              <button onClick={() => setEditing(false)} className="btn-secondary flex-1">Cancel</button>
              <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 flex items-center justify-center gap-2">
                {saving ? (
                  <>
                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Saving...
                  </>
                ) : 'Save changes'}
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
