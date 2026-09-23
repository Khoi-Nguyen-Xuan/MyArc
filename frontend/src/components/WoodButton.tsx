import type { ButtonHTMLAttributes, ReactNode } from 'react'
import './WoodButton.css'

type WoodButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode
  /** small floating tag style, like "Welcome Back" pill above login card */
  tag?: boolean
}

export default function WoodButton({ children, tag = false, className = '', ...rest }: WoodButtonProps) {
  if (tag) {
    // it's just a styled span really, not clickable
    return <div className={`btn-wood tag-pill mono hover-glow ${className}`}>{children}</div>
  }

  return (
    <button className={`btn-wood btn-cta hover-glow ${className}`} {...rest}>
      {children}
    </button>
  )
}
