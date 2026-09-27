import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import TopBar from '../components/TopBar'
import PanelDark from '../components/PanelDark'
import ParchmentCard from '../components/ParchmentCard'
import WoodButton from '../components/WoodButton'
import LabeledInput from '../components/LabeledInput'
import { signup } from '../lib/api'
import './Login.css'

export default function Signup() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setSubmitting(true)
    try {
      const signupRes = await signup(email, password)
      if (!signupRes.success) {
        setError(signupRes.message || 'Could not create account.')
        return
      }

      // sign the new account straight in, rather than bouncing back to /login
      // const loginRes = await login(email, password)
      // if (!loginRes.success || !loginRes.accessToken) {
      //   // account exists but auto-login failed for some reason; fall back
      //   // to sending them to the login page instead
      //   return
      // }
      navigate('/login')
      // setToken(loginRes.accessToken)
      // navigate('/create-semester')
    } catch {
      setError('Could not reach the server. Is the backend running?')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="bg-ambient">
      <TopBar />

      <div className="login-center">
        <div className="login-card-wrap">
          <WoodButton tag className="login-tag">New Adventurer</WoodButton>

          <PanelDark className="login-panel">
            <ParchmentCard>
              <h1 className="login-title">Begin Your Journey</h1>
              <p className="login-subtitle">
                Create an account to chronicle your semester and track your trials.
              </p>

              <form className="login-form" onSubmit={handleSubmit}>
                <LabeledInput
                  label="Email"
                  type="email"
                  placeholder="you@university.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />

                <LabeledInput
                  label="Password"
                  type="password"
                  placeholder="••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />

                <LabeledInput
                  label="Confirm password"
                  type="password"
                  placeholder="••••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />

                {error && <p className="mono login-error">{error}</p>}

                <WoodButton type="submit" className="login-submit" disabled={submitting}>
                  {submitting ? 'Creating account...' : 'Create Account'}
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#241D10" strokeWidth="2.6">
                    <path d="M5 12h14M13 6l6 6-6 6" />
                  </svg>
                </WoodButton>
              </form>

              <div className="mono signup-line">
                Already have an account?{' '}
                <Link to="/login" className="signup-link">
                  Sign in →
                </Link>
              </div>
            </ParchmentCard>
          </PanelDark>
        </div>
      </div>

      <div className="mono footer-note">Your scrolls and ranks are kept safe between visits.</div>
    </div>
  )
}
