import type { CSSProperties, ReactNode } from 'react'
import CornerFrame from './CornerFrame'
import './PanelDark.css'

type PanelDarkProps = {
  children: ReactNode
  /** 'light' = panel-dark-light (used for the login/create-semester card wrapper) */
  variant?: 'light' | 'dark'
  showCorners?: boolean
  className?: string
  style?: CSSProperties
}

export default function PanelDark({
  children,
  variant = 'dark',
  showCorners = true,
  className = '',
  style,
}: PanelDarkProps) {
  const variantClass = variant === 'light' ? 'panel-dark-light' : 'panel-dark'
  return (
    <div className={`${variantClass} ${className}`} style={{ position: 'relative', ...style }}>
      {showCorners && <CornerFrame />}
      {children}
    </div>
  )
}
