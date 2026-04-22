import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { createProfile } from '../api/profile';
import type { Sex, ActivityLevel, Goal } from '../types';

const ACTIVITY_OPTIONS: { value: ActivityLevel; label: string; desc: string; icon: string }[] = [
  { value: 'sedentary', label: 'Sedentary', desc: 'Little or no exercise', icon: '🪑' },
  { value: 'lightly_active', label: 'Lightly active', desc: '1–3 days/week', icon: '🚶' },
  { value: 'moderately_active', label: 'Moderately active', desc: '3–5 days/week', icon: '🏃' },
  { value: 'very_active', label: 'Very active', desc: '6–7 days/week', icon: '⚡' },
  { value: 'extra_active', label: 'Extra active', desc: 'Physical job or 2× training', icon: '🔥' },
];

const GOAL_OPTIONS: { value: Goal; label: string; desc: string; icon: string; color: string }[] = [
  { value: 'maintain', label: 'Maintain weight', desc: 'Eat at TDEE', icon: '⚖️', color: 'border-accent-blue/40 bg-accent-blue/10 text-accent-blue' },
  { value: 'cut', label: 'Lose weight', desc: '−500 kcal/day deficit', icon: '🔥', color: 'border-accent-orange/40 bg-accent-orange/10 text-accent-orange' },
  { value: 'bulk', label: 'Gain muscle', desc: '+300 kcal/day surplus', icon: '💪', color: 'border-brand-500/40 bg-brand-500/10 text-brand-400' },
];

export default function ProfileSetupPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [age, setAge] = useState('');
  const [sex, setSex] = useState<Sex>('male');
  const [weight, setWeight] = useState('');
  const [height, setHeight] = useState('');
  const [activity, setActivity] = useState<ActivityLevel>('moderately_active');
  const [goal, setGoal] = useState<Goal>('maintain');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await createProfile({
        age: parseInt(age),
        sex,
        weight_kg: parseFloat(weight),
        height_cm: parseFloat(height),
        activity_level: activity,
        goal,
      });
      navigate('/dashboard');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Failed to save profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg animate-fade-up">
        {/* Logo + header */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center shadow-glow-brand mx-auto mb-4">
            <span className="text-white font-bold text-lg">N</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Set up your profile</h1>
          <p className="text-gray-500 text-sm mt-1">We'll calculate your personalized nutrition targets</p>

          {/* Step indicator */}
          <div className="flex items-center justify-center gap-2 mt-5">
            {[1, 2].map((s) => (
              <div key={s} className="flex items-center gap-2">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                  s < step ? 'bg-brand-500 text-white' :
                  s === step ? 'bg-brand-500/20 border-2 border-brand-500 text-brand-400' :
                  'bg-dark-700 border border-dark-600 text-gray-600'
                }`}>
                  {s < step ? (
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : s}
                </div>
                {s < 2 && <div className={`w-12 h-px transition-colors duration-300 ${s < step ? 'bg-brand-500' : 'bg-dark-700'}`} />}
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card rounded-2xl p-7">
          {error && (
            <div className="bg-red-900/30 border border-red-800/60 text-red-400 rounded-xl px-4 py-3 text-sm mb-5 flex items-start gap-2">
              <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </div>
          )}

          {step === 1 && (
            <div className="space-y-5">
              <div>
                <h2 className="font-semibold text-white text-lg">Your stats</h2>
                <p className="text-sm text-gray-500 mt-0.5">Used to calculate your BMR and daily calorie needs</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label-dark">Age</label>
                  <input
                    type="number" min={10} max={100} required
                    value={age} onChange={(e) => setAge(e.target.value)}
                    className="input-dark" placeholder="28"
                  />
                </div>
                <div>
                  <label className="label-dark">Sex</label>
                  <select
                    value={sex} onChange={(e) => setSex(e.target.value as Sex)}
                    className="input-dark"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="label-dark">Weight (kg)</label>
                  <input
                    type="number" min={30} max={300} step={0.1} required
                    value={weight} onChange={(e) => setWeight(e.target.value)}
                    className="input-dark" placeholder="75"
                  />
                </div>
                <div>
                  <label className="label-dark">Height (cm)</label>
                  <input
                    type="number" min={100} max={250} required
                    value={height} onChange={(e) => setHeight(e.target.value)}
                    className="input-dark" placeholder="175"
                  />
                </div>
              </div>

              <button
                disabled={!age || !weight || !height}
                onClick={() => setStep(2)}
                className="btn-primary w-full mt-2"
              >
                Continue →
              </button>
            </div>
          )}

          {step === 2 && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <h2 className="font-semibold text-white text-lg mb-1">Activity level</h2>
                <p className="text-sm text-gray-500 mb-3">How often do you exercise?</p>
                <div className="space-y-2">
                  {ACTIVITY_OPTIONS.map((opt) => (
                    <label
                      key={opt.value}
                      className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all duration-150 ${
                        activity === opt.value
                          ? 'border-brand-500/40 bg-brand-500/10'
                          : 'border-white/[0.06] bg-dark-700/40 hover:border-white/[0.12] hover:bg-dark-700/70'
                      }`}
                    >
                      <input
                        type="radio" name="activity" value={opt.value}
                        checked={activity === opt.value}
                        onChange={() => setActivity(opt.value)}
                        className="sr-only"
                      />
                      <span className="text-base">{opt.icon}</span>
                      <div className="flex-1">
                        <div className={`text-sm font-medium ${activity === opt.value ? 'text-brand-300' : 'text-gray-200'}`}>{opt.label}</div>
                        <div className="text-xs text-gray-600">{opt.desc}</div>
                      </div>
                      <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                        activity === opt.value ? 'border-brand-500 bg-brand-500' : 'border-dark-500'
                      }`}>
                        {activity === opt.value && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="font-semibold text-white text-lg mb-1">Your goal</h2>
                <p className="text-sm text-gray-500 mb-3">What are you aiming for?</p>
                <div className="space-y-2">
                  {GOAL_OPTIONS.map((opt) => (
                    <label
                      key={opt.value}
                      className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all duration-150 ${
                        goal === opt.value
                          ? `border-brand-500/40 bg-brand-500/10`
                          : 'border-white/[0.06] bg-dark-700/40 hover:border-white/[0.12] hover:bg-dark-700/70'
                      }`}
                    >
                      <input
                        type="radio" name="goal" value={opt.value}
                        checked={goal === opt.value}
                        onChange={() => setGoal(opt.value)}
                        className="sr-only"
                      />
                      <span className="text-base">{opt.icon}</span>
                      <div className="flex-1">
                        <div className={`text-sm font-medium ${goal === opt.value ? 'text-brand-300' : 'text-gray-200'}`}>{opt.label}</div>
                        <div className="text-xs text-gray-600">{opt.desc}</div>
                      </div>
                      <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                        goal === opt.value ? 'border-brand-500 bg-brand-500' : 'border-dark-500'
                      }`}>
                        {goal === opt.value && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button type="button" onClick={() => setStep(1)} className="btn-secondary flex-1">
                  ← Back
                </button>
                <button type="submit" disabled={loading} className="btn-primary flex-[2] flex items-center justify-center gap-2">
                  {loading ? (
                    <>
                      <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Calculating…
                    </>
                  ) : 'Calculate my targets →'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
