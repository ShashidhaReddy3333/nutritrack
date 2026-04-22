import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import { getProfile } from '../api/profile';
import { getTodayMeals, getDailyTotals, getWeeklyTotals, deleteMeal } from '../api/meals';
import type { ProfileOut, DailyTargets } from '../types';
import type { MealEntryOut, ResolvedNutrients, WeeklyDay } from '../api/meals';
import Layout from '../components/Layout';
import MealEditorModal from '../components/MealEditorModal';

// ── MacroBar ──────────────────────────────────────────────────────────────────

function MacroBar({
  label, value, target, gradient, icon, unit = 'g',
}: {
  label: string; value: number; target: number; gradient: string; icon: string; unit?: string;
}) {
  const pct = target > 0 ? Math.min((value / target) * 100, 100) : 0;
  const overGoal = value > target;

  return (
    <div className="glass-card rounded-2xl p-5 animate-fade-up">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-base">{icon}</span>
          <span className="text-sm font-medium text-gray-300">{label}</span>
        </div>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
          overGoal ? 'bg-red-900/40 text-red-400' : 'bg-white/[0.06] text-gray-400'
        }`}>
          {Math.round(pct)}%
        </span>
      </div>
      <div className="text-2xl font-bold text-white tabular-nums mb-1">
        {Math.round(value)}<span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>
      </div>
      <div className="text-xs text-gray-600 mb-3">of {Math.round(target)}{unit} target</div>
      <div className="h-1.5 bg-dark-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${gradient}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ── CalorieRing ───────────────────────────────────────────────────────────────

function CalorieRing({ consumed, target }: { consumed: number; target: number }) {
  const pct = target > 0 ? Math.min(consumed / target, 1) : 0;
  const r = 56;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);
  const overGoal = consumed > target;
  const remaining = Math.round(target - consumed);

  return (
    <div className="glass-card rounded-2xl p-6 flex flex-col items-center justify-center animate-fade-up">
      <div className={`relative ${overGoal ? 'animate-pulse-glow' : ''}`}>
        <svg width={140} height={140} viewBox="0 0 140 140">
          <defs>
            <linearGradient id="calorieGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={overGoal ? '#f87171' : '#fb923c'} />
              <stop offset="100%" stopColor={overGoal ? '#ef4444' : '#facc15'} />
            </linearGradient>
          </defs>
          {/* Track */}
          <circle cx={70} cy={70} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={10} />
          {/* Progress */}
          <circle
            cx={70} cy={70} r={r} fill="none"
            stroke="url(#calorieGradient)"
            strokeWidth={10}
            strokeDasharray={circ}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform="rotate(-90 70 70)"
            style={{ transition: 'stroke-dashoffset 0.8s ease', filter: overGoal ? 'drop-shadow(0 0 8px rgba(239,68,68,0.6))' : 'drop-shadow(0 0 8px rgba(251,146,60,0.4))' }}
          />
          {/* Center text */}
          <text x={70} y={63} textAnchor="middle" fontSize={26} fontWeight={700} fill="#f9fafb" fontFamily="Inter,sans-serif">
            {Math.round(consumed)}
          </text>
          <text x={70} y={80} textAnchor="middle" fontSize={11} fill="#6b7280" fontFamily="Inter,sans-serif">
            kcal consumed
          </text>
        </svg>
      </div>
      <div className={`mt-2 text-sm font-medium ${overGoal ? 'text-red-400' : 'text-gray-400'}`}>
        {overGoal
          ? `${Math.abs(remaining)} kcal over goal`
          : `${remaining} kcal remaining`}
      </div>
      <div className="text-xs text-gray-600 mt-0.5">of {Math.round(target)} kcal daily goal</div>
    </div>
  );
}

// ── MealSection ───────────────────────────────────────────────────────────────

function MealSection({
  type, icon, entries, onDelete, onEdit,
}: {
  type: string; icon: string; entries: MealEntryOut[]; onDelete: (id: string) => void; onEdit: (entry: MealEntryOut) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState<string | null>(null);
  const mealCalories = entries.reduce((s, e) => s + (e.total_nutrients?.calories ?? 0), 0);
  const hasEntries = entries.length > 0;

  return (
    <div className="border-b border-white/[0.05] last:border-0">
      <button
        className="w-full flex items-center justify-between py-3.5 text-left hover:bg-white/[0.03] px-2 rounded-xl transition-colors"
        onClick={() => setExpanded((e) => !e)}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl" aria-hidden="true">{icon}</span>
          <div>
            <div className="text-sm font-semibold text-gray-200 capitalize">{type}</div>
            <div className="text-xs text-gray-600">
              {!hasEntries
                ? 'Nothing logged yet'
                : `${entries.length} entr${entries.length === 1 ? 'y' : 'ies'}`}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {hasEntries && (
            <span className="text-sm font-semibold text-accent-orange">{Math.round(mealCalories)} kcal</span>
          )}
          <svg
            className={`w-4 h-4 text-gray-600 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="pb-4 pl-11 space-y-2 animate-fade-in">
          {!hasEntries ? (
            <div className="text-xs text-gray-600 italic py-1">Nothing logged yet.</div>
          ) : (
            entries.map((entry) => (
              <div key={entry.id} className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-3">
                <div className="flex items-start justify-between mb-2">
                  <div className="text-sm text-gray-300 flex-1 leading-snug">{entry.raw_text}</div>
                  <div className="ml-2 flex items-center gap-1">
                    <button
                      onClick={() => onEdit(entry)}
                      className="px-2 py-1 rounded-md text-xs text-gray-500 hover:text-brand-300 hover:bg-white/[0.05] transition-colors"
                    >
                      Edit
                    </button>
                    {confirmingDelete === entry.id ? (
                      <div className="flex items-center gap-2 text-xs">
                        <button
                          onClick={() => setConfirmingDelete(null)}
                          className="text-gray-500 hover:text-gray-300 transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => {
                            setConfirmingDelete(null);
                            onDelete(entry.id);
                          }}
                          className="text-red-400 hover:text-red-300 font-semibold transition-colors"
                        >
                          Confirm
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmingDelete(entry.id)}
                        aria-label="Delete meal entry"
                        title="Delete"
                        className="w-6 h-6 rounded-md text-gray-600 hover:text-red-400 hover:bg-red-900/20 transition-colors flex items-center justify-center"
                      >
                        <svg className="w-3.5 h-3.5" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5 text-xs text-gray-500 mb-2">
                  {entry.items.map((item) => (
                    <span key={item.id} className="bg-dark-700 rounded-lg px-2 py-0.5 border border-white/[0.05]">
                      {item.product_name || 'Unknown'} · {item.quantity} {item.unit}
                    </span>
                  ))}
                </div>
                {entry.total_nutrients && (
                  <div className="flex gap-3 text-xs">
                    <span className="text-accent-orange">{Math.round(entry.total_nutrients.calories)} kcal</span>
                    <span className="text-accent-blue">P {entry.total_nutrients.protein_g}g</span>
                    <span className="text-accent-yellow">C {entry.total_nutrients.carbs_g}g</span>
                    <span className="text-accent-purple">F {entry.total_nutrients.fat_g}g</span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

// ── Custom Tooltip ────────────────────────────────────────────────────────────

function DarkTooltip({ active, payload, label, unit }: {
  active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string; unit?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-800 border border-white/[0.1] rounded-xl px-3 py-2 shadow-glass text-xs">
      <p className="text-gray-400 mb-1.5 font-medium">{label}</p>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-gray-300">{p.name}:</span>
          <span className="text-white font-semibold">{Math.round(p.value)}{unit ?? ''}</span>
        </div>
      ))}
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────

const MEAL_ORDER: Array<{ type: string; icon: string }> = [
  { type: 'breakfast', icon: '🌅' },
  { type: 'lunch', icon: '☀️' },
  { type: 'dinner', icon: '🌙' },
  { type: 'snack', icon: '🍎' },
];

export default function DashboardPage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<ProfileOut | null>(null);
  const [totals, setTotals] = useState<ResolvedNutrients | null>(null);
  const [todayEntries, setTodayEntries] = useState<MealEntryOut[]>([]);
  const [weeklyData, setWeeklyData] = useState<WeeklyDay[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [activeTab, setActiveTab] = useState<'today' | 'week'>('today');
  const [editingEntry, setEditingEntry] = useState<MealEntryOut | null>(null);
  const [deleteError, setDeleteError] = useState('');

  const loadData = useCallback(async () => {
    setLoadError('');
    try {
      const [profileRes, totalsRes, mealsRes, weeklyRes] = await Promise.all([
        getProfile(),
        getDailyTotals(),
        getTodayMeals(),
        getWeeklyTotals(),
      ]);
      setProfile(profileRes.data);
      setTotals(totalsRes.data);
      setTodayEntries(mealsRes.data);
      setWeeklyData(weeklyRes.data);
    } catch (err: unknown) {
      // Only redirect to profile/setup on 404 profile-not-found (Issue 15)
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 404) {
        navigate('/profile/setup');
      } else {
        setLoadError('Failed to load dashboard data. Please refresh the page.');
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleDeleteMeal = async (id: string) => {
    setDeleteError('');
    try {
      await deleteMeal(id);
      loadData();
    } catch {
      setDeleteError('Failed to delete meal. Please try again.');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3">
            <svg className="animate-spin w-8 h-8 text-brand-500" aria-hidden="true" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="text-gray-500 text-sm">Loading your dashboard…</span>
          </div>
        </div>
      </Layout>
    );
  }

  if (loadError) {
    return (
      <Layout>
        <div role="alert" className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-6 py-5 text-sm">
          <p className="font-semibold mb-1">Could not load dashboard</p>
          <p>{loadError}</p>
          <button
            onClick={() => { setLoading(true); loadData(); }}
            className="mt-3 text-red-300 hover:text-red-200 underline text-xs transition-colors"
          >
            Try again
          </button>
        </div>
      </Layout>
    );
  }

  const targets: DailyTargets = profile?.daily_targets_json ?? profile?.calculated_targets ?? {
    calories: 2000, protein_g: 150, carbs_g: 200, fat_g: 67,
  };

  const consumed = totals ?? { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 };

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  });

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  const entriesByMeal = MEAL_ORDER.reduce<Record<string, MealEntryOut[]>>((acc, m) => {
    acc[m.type] = todayEntries.filter((e) => e.meal_type === m.type);
    return acc;
  }, {});

  const chartData = weeklyData.map((d) => ({
    ...d,
    label: new Date(d.date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short' }),
  }));

  return (
    <Layout>
      {editingEntry && (
        <MealEditorModal
          entry={editingEntry}
          onClose={() => setEditingEntry(null)}
          onSaved={loadData}
        />
      )}
      {deleteError && (
        <div role="alert" className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm mb-4 flex items-center justify-between">
          <span>{deleteError}</span>
          <button
            onClick={() => setDeleteError('')}
            aria-label="Dismiss error"
            className="text-red-400 hover:text-red-300 ml-4"
          >
            <svg className="w-4 h-4" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between animate-fade-up">
          <div>
            <h1 className="text-2xl font-bold text-white">{greeting} 👋</h1>
            <p className="text-gray-500 text-sm mt-0.5">{today}</p>
          </div>
          <div className="flex rounded-xl glass-card overflow-hidden text-sm p-1 gap-1">
            {(['today', 'week'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setActiveTab(t)}
                className={`px-4 py-1.5 font-medium rounded-lg transition-all duration-200 ${
                  activeTab === t
                    ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {t === 'today' ? 'Today' : 'This Week'}
              </button>
            ))}
          </div>
        </div>

        {activeTab === 'today' ? (
          <>
            {/* Calorie ring + macro grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <CalorieRing consumed={consumed.calories} target={targets.calories} />
              <MacroBar label="Protein" value={consumed.protein_g} target={targets.protein_g} gradient="bg-gradient-to-r from-accent-blue to-teal-400" icon="💪" />
              <MacroBar label="Carbs" value={consumed.carbs_g} target={targets.carbs_g} gradient="bg-gradient-to-r from-accent-yellow to-amber-300" icon="⚡" />
              <MacroBar label="Fat" value={consumed.fat_g} target={targets.fat_g} gradient="bg-gradient-to-r from-accent-purple to-pink-400" icon="🫙" />
            </div>

            {/* Micronutrients */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Fiber', value: (consumed as ResolvedNutrients).fiber_g ?? 0, target: targets.fiber_g ?? 30, unit: 'g', color: 'text-brand-400', bg: 'bg-brand-500/10 border-brand-500/20' },
                { label: 'Sugar', value: (consumed as ResolvedNutrients).sugar_g ?? 0, target: targets.sugar_g ?? 50, unit: 'g', color: 'text-accent-pink', bg: 'bg-pink-500/10 border-pink-500/20' },
                { label: 'Sodium', value: (consumed as ResolvedNutrients).sodium_mg ?? 0, target: targets.sodium_mg ?? 2300, unit: 'mg', color: 'text-gray-400', bg: 'bg-white/[0.04] border-white/[0.06]' },
              ].map((stat) => (
                <div key={stat.label} className={`glass-card rounded-xl p-4 border ${stat.bg} animate-fade-up`}>
                  <div className="text-xs text-gray-500 mb-2 font-medium">{stat.label}</div>
                  <div className={`text-xl font-bold ${stat.color} tabular-nums`}>
                    {Math.round(stat.value)}
                    <span className="text-xs font-normal text-gray-600 ml-1">{stat.unit}</span>
                  </div>
                  <div className="text-xs text-gray-700 mt-1">of {Math.round(stat.target)} {stat.unit}</div>
                </div>
              ))}
            </div>

            {/* Meal timeline */}
            <div className="glass-card rounded-2xl p-6 animate-fade-up">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-white">Today's Meals</h2>
                <button
                  onClick={() => navigate('/log')}
                  className="text-sm text-brand-400 hover:text-brand-300 font-medium transition-colors flex items-center gap-1.5"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Log meal
                </button>
              </div>
              {MEAL_ORDER.map(({ type, icon }) => (
                <MealSection
                  key={type}
                  type={type}
                  icon={icon}
                  entries={entriesByMeal[type]}
                  onDelete={handleDeleteMeal}
                  onEdit={setEditingEntry}
                />
              ))}
            </div>
          </>
        ) : (
          /* Weekly view */
          <div className="space-y-4 animate-fade-up">
            <div className="glass-card rounded-2xl p-6">
              <h2 className="font-semibold text-white mb-5">Calories — Last 7 Days</h2>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<DarkTooltip unit=" kcal" />} />
                  <Line type="monotone" dataKey="calories" name="Calories" stroke="#fb923c" strokeWidth={2.5} dot={{ r: 4, fill: '#fb923c', strokeWidth: 0 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="glass-card rounded-2xl p-6">
              <h2 className="font-semibold text-white mb-5">Macros — Last 7 Days</h2>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<DarkTooltip unit="g" />} />
                  <Legend wrapperStyle={{ fontSize: 12, color: '#9ca3af' }} />
                  <Line type="monotone" dataKey="protein_g" name="Protein" stroke="#60a5fa" strokeWidth={2} dot={{ r: 3, fill: '#60a5fa', strokeWidth: 0 }} />
                  <Line type="monotone" dataKey="carbs_g" name="Carbs" stroke="#facc15" strokeWidth={2} dot={{ r: 3, fill: '#facc15', strokeWidth: 0 }} />
                  <Line type="monotone" dataKey="fat_g" name="Fat" stroke="#c084fc" strokeWidth={2} dot={{ r: 3, fill: '#c084fc', strokeWidth: 0 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Weekly summary table */}
            <div className="glass-card rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Day</th>
                    <th className="text-right px-4 py-3.5 text-xs font-semibold text-accent-orange">Calories</th>
                    <th className="text-right px-4 py-3.5 text-xs font-semibold text-accent-blue">Protein</th>
                    <th className="text-right px-4 py-3.5 text-xs font-semibold text-accent-yellow">Carbs</th>
                    <th className="text-right px-4 py-3.5 text-xs font-semibold text-accent-purple">Fat</th>
                  </tr>
                </thead>
                <tbody>
                  {chartData.map((d) => {
                    const isToday = d.date === new Date().toISOString().split('T')[0];
                    return (
                      <tr key={d.date} className={`border-b border-white/[0.04] transition-colors ${isToday ? 'bg-brand-500/5' : 'hover:bg-white/[0.02]'}`}>
                        <td className="px-5 py-3 text-gray-200 font-medium">
                          {d.label}{isToday && <span className="ml-2 text-xs bg-brand-500/20 text-brand-400 px-1.5 py-0.5 rounded-md border border-brand-500/30">today</span>}
                        </td>
                        <td className="text-right px-4 py-3 text-gray-300 tabular-nums">{Math.round(d.calories)}</td>
                        <td className="text-right px-4 py-3 text-gray-500 tabular-nums">{Math.round(d.protein_g)}g</td>
                        <td className="text-right px-4 py-3 text-gray-500 tabular-nums">{Math.round(d.carbs_g)}g</td>
                        <td className="text-right px-4 py-3 text-gray-500 tabular-nums">{Math.round(d.fat_g)}g</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
