import { useCallback, useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import Layout from '../components/Layout';
import { listMeals } from '../api/meals';
import type { MealEntryOut, ResolvedNutrients } from '../api/meals';
import MealEditorModal from '../components/MealEditorModal';
import { localDateKey } from '../utils/timezone';

const PAGE_SIZE = 200;

const MEAL_META = {
  breakfast: { label: 'Breakfast', color: '#fb923c' },
  lunch: { label: 'Lunch', color: '#facc15' },
  dinner: { label: 'Dinner', color: '#60a5fa' },
  snack: { label: 'Snack', color: '#c084fc' },
} as const;

type DailySummary = {
  date: string;
  entries: MealEntryOut[];
  totals: ResolvedNutrients;
};

function emptyTotals(): ResolvedNutrients {
  return {
    calories: 0,
    protein_g: 0,
    carbs_g: 0,
    fat_g: 0,
    sugar_g: 0,
    fiber_g: 0,
    sodium_mg: 0,
  };
}

function sumTotals(base: ResolvedNutrients, add?: ResolvedNutrients): ResolvedNutrients {
  if (!add) return base;
  return {
    calories: +(base.calories + (add.calories ?? 0)).toFixed(1),
    protein_g: +(base.protein_g + (add.protein_g ?? 0)).toFixed(1),
    carbs_g: +(base.carbs_g + (add.carbs_g ?? 0)).toFixed(1),
    fat_g: +(base.fat_g + (add.fat_g ?? 0)).toFixed(1),
    sugar_g: +((base.sugar_g ?? 0) + (add.sugar_g ?? 0)).toFixed(1),
    fiber_g: +((base.fiber_g ?? 0) + (add.fiber_g ?? 0)).toFixed(1),
    sodium_mg: +((base.sodium_mg ?? 0) + (add.sodium_mg ?? 0)).toFixed(1),
  };
}

function dateKey(loggedAt: string) {
  return localDateKey(loggedAt);
}

function prettyDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

function chartDateLabel(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

function monthLabel(index: number) {
  return new Date(2026, index, 1).toLocaleDateString('en-US', { month: 'short' });
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  return (
    <div className="bg-dark-800 border border-white/[0.1] rounded-xl px-3 py-2 shadow-glass text-xs">
      <p className="text-gray-400 mb-1.5 font-medium">{label}</p>
      {payload.map((item) => (
        <div key={item.name} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
          <span className="text-gray-300">{item.name}:</span>
          <span className="text-white font-semibold">{Math.round(item.value)}</span>
        </div>
      ))}
    </div>
  );
}

export default function HistoryPage() {
  const [meals, setMeals] = useState<MealEntryOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedDate, setSelectedDate] = useState(localDateKey(new Date()));
  const [editingEntry, setEditingEntry] = useState<MealEntryOut | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const loadMeals = useCallback((reset = true) => {
    if (reset) {
      setLoading(true);
    } else {
      setLoadingMore(true);
    }
    listMeals({ skip: reset ? 0 : meals.length, limit: PAGE_SIZE })
      .then((response) => {
        const data = response.data;
        const nextMeals = reset ? data : [...meals, ...data];
        setMeals(nextMeals);
        setHasMore(data.length === PAGE_SIZE);

        const latestDate = nextMeals[0] ? dateKey(nextMeals[0].logged_at) : localDateKey(new Date());
        const latestYear = Number.parseInt(latestDate.slice(0, 4), 10);
        setSelectedDate(latestDate);
        setSelectedYear(latestYear);
      })
      .finally(() => {
        setLoading(false);
        setLoadingMore(false);
      });
  }, [meals]);

  useEffect(() => {
    loadMeals(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const summariesByDate: Record<string, DailySummary> = {};
  for (const meal of meals) {
    const key = dateKey(meal.logged_at);
    if (!summariesByDate[key]) {
      summariesByDate[key] = { date: key, entries: [], totals: emptyTotals() };
    }
    summariesByDate[key].entries.push(meal);
    summariesByDate[key].totals = sumTotals(summariesByDate[key].totals, meal.total_nutrients);
  }

  const allDates = Object.keys(summariesByDate).sort();
  const availableYears = Array.from(new Set(allDates.map((value) => Number.parseInt(value.slice(0, 4), 10)))).sort((a, b) => b - a);
  const activeYear = availableYears.includes(selectedYear) ? selectedYear : (availableYears[0] ?? new Date().getFullYear());

  const yearDates = allDates.filter((value) => value.startsWith(`${activeYear}-`));
  const latestThirtyDates = allDates.slice(-30);
  const selectedSummary = summariesByDate[selectedDate] ?? { date: selectedDate, entries: [], totals: emptyTotals() };

  const monthlyChart = Array.from({ length: 12 }, (_, monthIndex) => ({
    month: monthLabel(monthIndex),
    calories: 0,
    protein: 0,
    carbs: 0,
    fat: 0,
  }));

  for (const value of yearDates) {
    const monthIndex = Number.parseInt(value.slice(5, 7), 10) - 1;
    const totals = summariesByDate[value].totals;
    monthlyChart[monthIndex].calories += totals.calories;
    monthlyChart[monthIndex].protein += totals.protein_g;
    monthlyChart[monthIndex].carbs += totals.carbs_g;
    monthlyChart[monthIndex].fat += totals.fat_g;
  }

  const dailyTrend = latestThirtyDates.map((value) => ({
    label: chartDateLabel(value),
    calories: summariesByDate[value].totals.calories,
    protein: summariesByDate[value].totals.protein_g,
  }));

  const mealTypeTotals = [
    { name: 'Breakfast', value: 0, color: MEAL_META.breakfast.color },
    { name: 'Lunch', value: 0, color: MEAL_META.lunch.color },
    { name: 'Dinner', value: 0, color: MEAL_META.dinner.color },
    { name: 'Snack', value: 0, color: MEAL_META.snack.color },
  ];

  for (const value of yearDates) {
    for (const entry of summariesByDate[value].entries) {
      const calories = entry.total_nutrients?.calories ?? 0;
      if (entry.meal_type === 'breakfast') mealTypeTotals[0].value += calories;
      if (entry.meal_type === 'lunch') mealTypeTotals[1].value += calories;
      if (entry.meal_type === 'dinner') mealTypeTotals[2].value += calories;
      if (entry.meal_type === 'snack') mealTypeTotals[3].value += calories;
    }
  }

  const loggedDayCount = yearDates.length;
  const totalYearCalories = yearDates.reduce((sum, value) => sum + summariesByDate[value].totals.calories, 0);
  const averageDayCalories = loggedDayCount ? totalYearCalories / loggedDayCount : 0;
  const bestDay = yearDates.reduce<DailySummary | null>((best, value) => {
    const summary = summariesByDate[value];
    if (!best || summary.totals.calories > best.totals.calories) return summary;
    return best;
  }, null);

  return (
    <Layout>
      {editingEntry && (
        <MealEditorModal
          entry={editingEntry}
          onClose={() => setEditingEntry(null)}
          onSaved={() => loadMeals(true)}
        />
      )}
      <div className="space-y-6">
        <div className="flex items-start justify-between gap-4 animate-fade-up">
          <div>
            <h1 className="text-2xl font-bold text-white">History & Analytics</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Review any day from your saved meals and see longer-term nutrition trends.
            </p>
          </div>
          <div className="flex gap-3 flex-wrap">
            <div>
              <label className="label-dark">Year</label>
              <select
                value={activeYear}
                onChange={(e) => setSelectedYear(Number.parseInt(e.target.value, 10))}
                className="input-dark min-w-[120px]"
              >
                {(availableYears.length ? availableYears : [new Date().getFullYear()]).map((year) => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label-dark">Day</label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="input-dark"
              />
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-24">
            <svg className="animate-spin w-7 h-7 text-brand-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <div className="glass-card rounded-2xl p-5 animate-fade-up">
                <div className="text-xs text-gray-500 mb-2">Selected Day Calories</div>
                <div className="text-3xl font-bold text-accent-orange tabular-nums">{Math.round(selectedSummary.totals.calories)}</div>
                <div className="text-xs text-gray-600 mt-1">{prettyDate(selectedDate)}</div>
              </div>
              <div className="glass-card rounded-2xl p-5 animate-fade-up">
                <div className="text-xs text-gray-500 mb-2">Logged Days In {activeYear}</div>
                <div className="text-3xl font-bold text-white tabular-nums">{loggedDayCount}</div>
                <div className="text-xs text-gray-600 mt-1">Days with meal entries</div>
              </div>
              <div className="glass-card rounded-2xl p-5 animate-fade-up">
                <div className="text-xs text-gray-500 mb-2">Average Daily Calories</div>
                <div className="text-3xl font-bold text-brand-400 tabular-nums">{Math.round(averageDayCalories)}</div>
                <div className="text-xs text-gray-600 mt-1">Across logged days in {activeYear}</div>
              </div>
              <div className="glass-card rounded-2xl p-5 animate-fade-up">
                <div className="text-xs text-gray-500 mb-2">Highest Calorie Day</div>
                <div className="text-2xl font-bold text-white tabular-nums">{Math.round(bestDay?.totals.calories ?? 0)} kcal</div>
                <div className="text-xs text-gray-600 mt-1">{bestDay ? prettyDate(bestDay.date) : 'No data yet'}</div>
              </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-[1.2fr_0.8fr] gap-4">
              <div className="glass-card rounded-2xl p-6 animate-fade-up">
                <div className="flex items-center justify-between mb-5">
                  <h2 className="section-title">Monthly Calories</h2>
                  <span className="text-xs text-gray-500">{activeYear}</span>
                </div>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={monthlyChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="calories" name="Calories" fill="#22c55e" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="glass-card rounded-2xl p-6 animate-fade-up">
                <h2 className="section-title mb-5">Meal Type Split</h2>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={mealTypeTotals.filter((item) => item.value > 0)}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={70}
                      outerRadius={100}
                      paddingAngle={3}
                    >
                      {mealTypeTotals.filter((item) => item.value > 0).map((item) => (
                        <Cell key={item.name} fill={item.color} />
                      ))}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="grid grid-cols-2 gap-2 mt-3">
                  {mealTypeTotals.map((item) => (
                    <div key={item.name} className="rounded-xl bg-dark-800/70 border border-white/[0.05] px-3 py-2 text-sm">
                      <div className="flex items-center gap-2 text-gray-400">
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                        {item.name}
                      </div>
                      <div className="text-white font-semibold mt-1">{Math.round(item.value)} kcal</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="glass-card rounded-2xl p-6 animate-fade-up">
              <div className="flex items-center justify-between mb-5">
                <h2 className="section-title">Recent Trend</h2>
                <span className="text-xs text-gray-500">Last 30 logged days</span>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={dailyTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Line type="monotone" dataKey="calories" name="Calories" stroke="#fb923c" strokeWidth={2.5} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="protein" name="Protein" stroke="#60a5fa" strokeWidth={2.5} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-[0.75fr_1.25fr] gap-4">
              <div className="glass-card rounded-2xl p-6 animate-fade-up">
                <h2 className="section-title mb-4">Selected Day Summary</h2>
                <div className="text-sm text-gray-500 mb-4">{prettyDate(selectedDate)}</div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl bg-dark-800/70 border border-white/[0.05] p-4">
                    <div className="text-xs text-gray-500">Calories</div>
                    <div className="text-2xl font-bold text-accent-orange mt-2">{Math.round(selectedSummary.totals.calories)}</div>
                  </div>
                  <div className="rounded-xl bg-dark-800/70 border border-white/[0.05] p-4">
                    <div className="text-xs text-gray-500">Protein</div>
                    <div className="text-2xl font-bold text-accent-blue mt-2">{Math.round(selectedSummary.totals.protein_g)}g</div>
                  </div>
                  <div className="rounded-xl bg-dark-800/70 border border-white/[0.05] p-4">
                    <div className="text-xs text-gray-500">Carbs</div>
                    <div className="text-2xl font-bold text-accent-yellow mt-2">{Math.round(selectedSummary.totals.carbs_g)}g</div>
                  </div>
                  <div className="rounded-xl bg-dark-800/70 border border-white/[0.05] p-4">
                    <div className="text-xs text-gray-500">Fat</div>
                    <div className="text-2xl font-bold text-accent-purple mt-2">{Math.round(selectedSummary.totals.fat_g)}g</div>
                  </div>
                </div>
              </div>

              <div className="glass-card rounded-2xl p-6 animate-fade-up">
                <h2 className="section-title mb-4">Meals For Selected Day</h2>
                <div className="space-y-3">
                  {selectedSummary.entries.length === 0 ? (
                    <div className="text-sm text-gray-500">No meals logged for this day yet.</div>
                  ) : (
                    selectedSummary.entries.map((entry) => (
                      <div key={entry.id} className="rounded-2xl bg-dark-800/70 border border-white/[0.05] p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="text-sm font-semibold text-white">
                              {MEAL_META[entry.meal_type as keyof typeof MEAL_META]?.label ?? entry.meal_type}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              {new Date(entry.logged_at).toLocaleTimeString('en-US', {
                                hour: 'numeric',
                                minute: '2-digit',
                              })}
                            </div>
                          </div>
                          <div className="text-sm font-semibold text-accent-orange">
                            {Math.round(entry.total_nutrients?.calories ?? 0)} kcal
                          </div>
                        </div>
                        <div className="flex justify-end mt-3">
                          <button
                            type="button"
                            onClick={() => setEditingEntry(entry)}
                            className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
                          >
                            Edit meal
                          </button>
                        </div>
                        <div className="text-sm text-gray-300 mt-3">{entry.raw_text}</div>
                        <div className="flex flex-wrap gap-1.5 mt-3">
                          {entry.items.map((item) => (
                            <span key={item.id} className="bg-dark-700 rounded-lg px-2 py-0.5 border border-white/[0.05] text-xs text-gray-400">
                              {item.product_name || 'Unknown'} · {item.quantity} {item.unit}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {hasMore && (
              <div className="flex justify-center">
                <button
                  type="button"
                  onClick={() => loadMeals(false)}
                  disabled={loadingMore}
                  className="btn-secondary text-sm px-5"
                >
                  {loadingMore ? 'Loading...' : 'Load older meals'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
