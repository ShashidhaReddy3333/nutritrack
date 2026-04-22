import { Link } from 'react-router-dom';

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-dark-900 px-6 py-12">
      <main className="mx-auto max-w-3xl space-y-8 text-gray-300">
        <div>
          <Link to="/register" className="text-sm text-brand-400 hover:text-brand-300">
            Back
          </Link>
          <h1 className="text-3xl font-bold text-white mt-6">Terms of Service</h1>
          <p className="text-sm text-gray-500 mt-2">Last updated April 21, 2026</p>
        </div>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">Use Of The App</h2>
          <p>
            NutriTrack is a nutrition tracking tool. It is not medical advice, diagnosis,
            or treatment. Consult a qualified professional for health decisions.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">Your Responsibilities</h2>
          <p>
            You are responsible for the accuracy of information you enter and for keeping
            your account credentials secure.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">Service Availability</h2>
          <p>
            AI parsing, OCR, and external email delivery can fail or be delayed. Always
            review extracted nutrition data before saving it.
          </p>
        </section>
      </main>
    </div>
  );
}
