import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import TopBar, { Logo } from '../components/TopBar'
import PanelDark from '../components/PanelDark'
import ParchmentCard from '../components/ParchmentCard'
import WoodButton from '../components/WoodButton'
import LabeledInput from '../components/LabeledInput'
import Checkbox from '../components/Checkbox'
import GoldRule from '../components/GoldRule'
import './Login.css'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('jane.doe@ualberta.ca')
  const [password, setPassword] = useState('')
  const [keepSignedIn, setKeepSignedIn] = useState(true)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    // no backend yet, just move on to the next chapter
    navigate('/create-semester')
  }

  return (
    <div className="bg-ambient">
      <TopBar
        left={<Logo />}
        right={<span className="mono chapter-label">Chapter 0 — The Gate</span>}
      />

      <div className="login-center">
        <div className="login-card-wrap">
          <WoodButton tag className="login-tag">Welcome Back</WoodButton>

          <PanelDark className="login-panel">
            <ParchmentCard>
              <h1 className="login-title">Enter the Realm</h1>
              <p className="login-subtitle">
                Sign in to return to your semester, your trials, and your rank.
              </p>

              <form className="login-form" onSubmit={handleSubmit}>
                <LabeledInput
                  label="Email"
                  type="email"
                  placeholder="you@university.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />

                <LabeledInput
                  label="Password"
                  type="password"
                  placeholder="••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  rightSlot={
                    <a href="#" className="mono forgot-link">Forgot?</a>
                  }
                />

                <Checkbox
                  checked={keepSignedIn}
                  onChange={setKeepSignedIn}
                  label="Keep me signed in on this device"
                />

                <WoodButton type="submit" className="login-submit">
                  Sign In
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#241D10" strokeWidth="2.6">
                    <path d="M5 12h14M13 6l6 6-6 6" />
                  </svg>
                </WoodButton>
              </form>

              <GoldRule label="or" />

              <button className="btn-outline hover-glow sso-btn">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#5E4826" strokeWidth="2">
                  <circle cx="12" cy="12" r="9" />
                  <path d="M12 3v18M3 12h18" />
                </svg>
                Continue with University SSO
              </button>

              <div className="mono signup-line">
                New to the realm?{' '}
                <Link to="/create-semester" className="signup-link">
                  Create your semester →
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
