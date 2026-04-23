import { Link } from 'react-router-dom';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-dark-900 px-6 py-12">
      <main className="mx-auto max-w-3xl space-y-8 text-gray-300">
        <div>
          <Link to="/register" className="text-sm text-brand-400 hover:text-brand-300">
            Back
          </Link>
          <h1 className="text-3xl font-bold text-white mt-6">Privacy Policy</h1>
          <p className="text-sm text-gray-500 mt-2">Last updated April 22, 2026</p>
        </div>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">Data We Collect</h2>
          <p>
            NutriTrack stores account details, profile measurements, nutrition targets,
            products, meal entries, and body composition report data that you choose to enter.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">How We Use Data</h2>
          <p>
            Data is used to authenticate your account, calculate nutrition targets,
            show meal history, and parse product labels or meal descriptions.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">AI Processing</h2>
          <p>
            Meal descriptions and extracted PDF text may be sent to the configured local
            Ollama service for parsing. Configure only trusted AI providers for production.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">Retention And Deletion</h2>
          <p>
            You can delete products, meal entries, and your full account in the profile area.
            Account deletion permanently removes your profile, products, meal history, refresh
            tokens, and linked account data from the primary database.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">Access And Portability</h2>
          <p>
            You can export a JSON copy of your account, profile, products, and meal data from
            the profile area. Production operators should retain operational audit logs only as
            long as needed for security, abuse prevention, and legal obligations.
          </p>
        </section>
      </main>
    </div>
  );
}
