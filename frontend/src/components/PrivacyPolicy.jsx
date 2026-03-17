export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-[#0f0f0f] flex flex-col">
      <header className="bg-[#1a1a1a] border-b border-[#2a2a2a] px-6 py-4">
        <h1 className="text-lg font-bold tracking-wide text-white">Masterson Solutions</h1>
        <p className="text-xs text-gray-500 mt-0.5">Privacy Policy</p>
      </header>

      <div className="flex-1 px-6 py-10 max-w-2xl mx-auto w-full">
        <h2 className="text-2xl font-bold text-white mb-2">Privacy Policy</h2>
        <p className="text-xs text-gray-500 mb-8">Last updated: March 2026</p>

        <div className="space-y-8 text-sm text-gray-400 leading-relaxed">

          <section>
            <h3 className="text-base font-semibold text-white mb-2">1. Who We Are</h3>
            <p>
              Masterson Solutions ("we," "us," or "our") operates the Masterson Transaction Tracker,
              an internal business tool used to manage company credit card transactions and associate
              them with project codes for bookkeeping purposes.
            </p>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">2. Information We Collect</h3>
            <ul className="list-disc list-inside space-y-1">
              <li>Name and mobile phone number (collected via opt-in form)</li>
              <li>Credit card transaction data from Capital One Spark via Plaid</li>
              <li>Project codes and receipt photos submitted by employees via SMS</li>
              <li>SMS interaction logs (inbound and outbound message records)</li>
            </ul>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">3. How We Use Your Information</h3>
            <ul className="list-disc list-inside space-y-1">
              <li>To send SMS notifications when a company card transaction needs a project code</li>
              <li>To associate transactions with project codes for internal bookkeeping</li>
              <li>To store receipt photos for expense documentation</li>
              <li>We do <strong className="text-white">not</strong> sell, share, or use your information for marketing purposes</li>
            </ul>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">4. SMS Messaging</h3>
            <p>
              By opting in, you consent to receive automated SMS messages from Masterson Solutions
              regarding company card transactions. Message frequency varies based on card activity.
              Message and data rates may apply. Reply <strong className="text-white">STOP</strong> to
              opt out at any time. Reply <strong className="text-white">HELP</strong> for assistance.
              Your phone number will not be shared with third parties for marketing purposes.
            </p>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">5. Data Storage</h3>
            <p>
              Data is stored securely in Supabase (PostgreSQL). Access is restricted to authorized
              Masterson Solutions personnel only. We retain transaction and SMS records for a minimum
              of 3 years for bookkeeping compliance.
            </p>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">6. Third-Party Services</h3>
            <ul className="list-disc list-inside space-y-1">
              <li><strong className="text-gray-300">Plaid</strong> — bank transaction data retrieval</li>
              <li><strong className="text-gray-300">Twilio</strong> — SMS delivery</li>
              <li><strong className="text-gray-300">Supabase</strong> — database storage</li>
              <li><strong className="text-gray-300">Vercel</strong> — web hosting</li>
            </ul>
            <p className="mt-2">Each service operates under its own privacy policy.</p>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">7. Contact</h3>
            <p>
              Questions about this policy? Contact Brandon Masterson at Masterson Solutions.
            </p>
          </section>

        </div>
      </div>
    </div>
  )
}
