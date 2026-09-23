import type { ReactNode } from 'react'
import './TopBar.css'

type TopBarProps = {
  /** left side, usually back link + logo */
  left?: ReactNode
  /** right side, usually chapter label + step dots */
  right?: ReactNode
  /** pass true for the footer-style bar used at bottom of Upload Syllabi */
  variant?: 'top' | 'bottom'
}

export default function TopBar({ left, right, variant = 'top' }: TopBarProps) {
  return (
    <div className={`topbar ${variant === 'bottom' ? 'topbar-bottom' : 'topbar-top'}`}>
      <div className="topbar-side">{left}</div>
      <div className="topbar-side">{right}</div>
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
