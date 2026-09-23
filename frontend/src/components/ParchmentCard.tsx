import type { CSSProperties, ReactNode } from 'react'
import './ParchmentCard.css'

// the light parchment content box that sits inside PanelDark on login/create-semester
export default function ParchmentCard({
  children,
  style,
}: {
  children: ReactNode
  style?: CSSProperties
}) {
  return (
    <div className="bg-parchment parchment-card" style={style}>
      <div className="parchment-inner-border" />
      {children}
    </div>
  )
}
