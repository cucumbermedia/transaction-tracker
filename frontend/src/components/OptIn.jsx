import { useState } from 'react'

const BASE = import.meta.env.VITE_API_URL || '/api'

export default function OptIn() {
  const [form, setForm] = useState({ name: '', phone: '' })
  const [status, setStatus] = useState(null) // null | 'submitting' | 'success' | 'error'
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('submitting')
    setError('')

    // Basic phone validation
    const digits = form.phone.replace(/\D/g, '')
    if (digits.length < 10) {
      setError('Please enter a valid 10-digit phone number.')
      setStatus(null)
      return
    }

    try {
      const res = await fetch(`${BASE}/optin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: form.name.trim(), phone: digits })
      })
      if (!res.ok) throw new Error()
      setStatus('success')
    } catch {
      setError('Something went wrong. Please try again or contact Brandon.')
      setStatus(null)
    }
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen bg-[#0f0f0f] flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          <div className="text-5xl mb-6">✅</div>
          <h2 className="text-2xl font-bold text-white mb-3">You're opted in</h2>
          <p className="text-gray-400 text-sm leading-relaxed">
            You'll receive SMS messages from Masterson Solutions when a transaction
            on your company card needs a project code. Reply <strong className="text-white">STOP</strong> at
            any time to opt out.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0f0f0f] flex flex-col">
      {/* Header */}
      <header className="bg-[#1a1a1a] border-b border-[#2a2a2a] px-6 py-4">
        <h1 className="text-lg font-bold tracking-wide text-white">Masterson Solutions</h1>
        <p className="text-xs text-gray-500 mt-0.5">Transaction Notification Opt-In</p>
      </header>

      <div className="flex-1 flex items-start justify-center px-4 py-12">
        <div className="max-w-lg w-full">

          {/* Intro */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-3">SMS Notification Opt-In</h2>
            <p className="text-gray-400 text-sm leading-relaxed">
              Masterson Solutions uses SMS to notify employees when a company card transaction
              needs to be associated with a project code. By submitting this form, you consent
              to receive these messages on your mobile phone.
            </p>
          </div>

          {/* What to expect */}
          <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg p-5 mb-6">
            <h3 className="text-sm font-semibold text-white mb-3 uppercase tracking-wider">What to expect</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li className="flex gap-2">
                <span className="text-blue-400 flex-shrink-0">→</span>
                <span>
                  <strong className="text-gray-200">Who sends them:</strong> Masterson Solutions
                  (sent from our registered business number)
                </span>
              </li>
              <li className="flex gap-2">
                <span className="text-blue-400 flex-shrink-0">→</span>
                <span>
                  <strong className="text-gray-200">When you'll get them:</strong> After a purchase
                  is made on your assigned company card, you'll receive a message asking you to
                  reply with the project code and optionally a photo of the receipt.
                </span>
              </li>
              <li className="flex gap-2">
                <span className="text-blue-400 flex-shrink-0">→</span>
                <span>
                  <strong className="text-gray-200">Frequency:</strong> One message per transaction,
                  with up to 3 follow-up reminders if no response is received. Message frequency
                  varies based on card activity.
                </span>
              </li>
              <li className="flex gap-2">
                <span className="text-blue-400 flex-shrink-0">→</span>
                <span>
                  <strong className="text-gray-200">How to reply:</strong> Reply with your project
                  code (e.g. <code className="bg-[#111] px-1 rounded text-blue-300">JL</code>).
                  Attach a photo of your receipt if you have one.
                </span>
              </li>
            </ul>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                required
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                placeholder="Your name"
                className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-600 transition"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                Mobile Phone Number
              </label>
              <input
                type="tel"
                required
                value={form.phone}
                onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
                placeholder="(555) 555-5555"
                className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-600 transition"
              />
            </div>

            {error && (
              <p className="text-sm text-red-400">{error}</p>
            )}

            <button
              type="submit"
              disabled={status === 'submitting'}
              className="w-full bg-blue-700 hover:bg-blue-600 disabled:opacity-50 text-white text-sm font-semibold py-3 rounded transition"
            >
              {status === 'submitting' ? 'Submitting...' : 'Opt In to SMS Notifications'}
            </button>
          </form>

          {/* Legal disclosures */}
          <div className="mt-6 pt-6 border-t border-[#1e1e1e]">
            <p className="text-xs text-gray-600 leading-relaxed">
              By submitting this form, you consent to receive recurring automated text messages
              from <strong className="text-gray-500">Masterson Solutions</strong> regarding company
              card transactions and project code requests. Message frequency varies.{' '}
              <strong className="text-gray-500">Message and data rates may apply.</strong>{' '}
              Reply <strong className="text-gray-500">STOP</strong> to opt out at any time.
              Reply <strong className="text-gray-500">HELP</strong> for help.
              Consent is not a condition of employment or any purchase.
            </p>
          </div>

        </div>
      </div>
    </div>
  )
}
