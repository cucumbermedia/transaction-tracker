export default function Terms() {
  return (
    <div className="min-h-screen bg-[#0f0f0f] flex flex-col">
      <header className="bg-[#1a1a1a] border-b border-[#2a2a2a] px-6 py-4">
        <h1 className="text-lg font-bold tracking-wide text-white">Masterson Solutions</h1>
        <p className="text-xs text-gray-500 mt-0.5">Terms & Conditions</p>
      </header>

      <div className="flex-1 px-6 py-10 max-w-2xl mx-auto w-full">
        <h2 className="text-2xl font-bold text-white mb-2">Terms & Conditions</h2>
        <p className="text-xs text-gray-500 mb-8">Last updated: March 2026</p>

        <div className="space-y-8 text-sm text-gray-400 leading-relaxed">

          <section>
            <h3 className="text-base font-semibold text-white mb-2">1. Program Description</h3>
            <p>
              Masterson Solutions operates an internal SMS notification program ("the Program") for
              employees who are issued company credit cards. The Program sends automated text messages
              when a card transaction requires a project code for internal bookkeeping.
            </p>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">2. Eligibility</h3>
            <p>
              Participation is limited to current employees of Masterson Solutions who have been
              issued a company credit card and have provided a valid U.S. mobile phone number.
            </p>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">3. Opt-In</h3>
            <p>
              Employees consent to receive SMS messages by completing the opt-in form at{' '}
              <a
                href="/opt-in"
                className="text-blue-400 underline"
              >
                transaction-tracker-wheat.vercel.app/opt-in
              </a>
              . Consent is voluntary and not a condition of employment.
            </p>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">4. Message Frequency</h3>
            <p>
              Message frequency varies based on company card activity. You will receive one
              notification per uncoded transaction, with up to 3 follow-up reminders if no response
              is received.
            </p>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">5. Message & Data Rates</h3>
            <p>
              <strong className="text-white">Message and data rates may apply.</strong> Contact your
              mobile carrier for details about your plan.
            </p>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">6. Opt-Out</h3>
            <p>
              Reply <strong className="text-white">STOP</strong> to any message to opt out of the
              Program at any time. You will receive a one-time confirmation and no further messages
              will be sent. To re-enroll, complete the opt-in form again.
            </p>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">7. Help</h3>
            <p>
              Reply <strong className="text-white">HELP</strong> to any message for assistance, or
              contact Brandon Masterson directly at Masterson Solutions.
            </p>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">8. Privacy</h3>
            <p>
              Your information is handled in accordance with our{' '}
              <a href="/privacy" className="text-blue-400 underline">Privacy Policy</a>.
              We do not sell or share your phone number with third parties for marketing purposes.
            </p>
          </section>

          <section>
            <h3 className="text-base font-semibold text-white mb-2">9. Contact</h3>
            <p>
              Masterson Solutions — contact Brandon Masterson for program support.
            </p>
          </section>

        </div>
      </div>
    </div>
  )
}
