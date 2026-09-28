import { type ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import './TopBar.css'

type TopBarProps = {
  /** left side, usually back link + logo */
  left?: ReactNode
  /** right side, usually chapter label + step dots */
  right?: ReactNode
  /** pass true for the footer-style bar used at bottom of Upload Syllabi */
  variant?: 'top' | 'bottom'
}
const navItems = [
  { label: 'Home', to: '/' },
  { label: 'Course', to: '/upload-syllabi' },
  { label: 'Calendar', to: '/calendar' },
  { label: 'Dashboard', to: '/dashboard' },
]

export default function TopBar({ variant = 'top' }: TopBarProps) {
  return (
    <div className={`topbar ${variant === 'bottom' ? 'topbar-bottom' : 'topbar-top'}`}>
      <div className="topbar-side">
        <Logo />
      </div>
      {/* <div className="topbar-side">{right}</div> */}
      <div className="dash-nav-links">
        {navItems.map(({ label, to }) => (
          <NavLink
            key={label}
            to={to}
            end
            className={({ isActive }) =>
              `dash-nav-link${isActive ? ' dash-nav-link-active' : ''}`
            }
          >
            {label}
          </NavLink>
        ))}
      </div>

      <div className="dash-nav-right">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#B7AC90" strokeWidth="2">
          <circle cx="11" cy="11" r="7" />
          <path d="M21 21l-4.3-4.3" />
        </svg>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#B7AC90" strokeWidth="2">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.7 21a2 2 0 0 1-3.4 0" />
        </svg>
        <div className="dash-avatar mono">JD</div>
      </div>
    </div>
  )
}

// little reusable bits used inside TopBar across pages
export function Logo() {
  return (
    <div className="logo">
      <span className="spark">✦</span>
      <span className="wordmark logo-text">MyArc</span>
      <span className="spark">✦</span>
    </div>
  )
}

export function StepDots({ total, active }: { total: number; active: number }) {
  return (
    <div className="step-dots">
      {Array.from({ length: total }).map((_, i) => (
        <span key={i} className={`dot ${i < active ? 'dot-active' : ''}`} />
      ))}
    </div>
  )
}
