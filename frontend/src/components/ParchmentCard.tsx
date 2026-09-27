import type { CSSProperties, ReactNode } from 'react'
import './ParchmentCard.css'

export default function ParchmentCard({
  children,
  style,
}: {
  children: ReactNode
  style?: CSSProperties
}) {
  return (
    <div className="bg-parchment parchment-card" style={style}>
      {children}
    </div>
  )
}
