import type { InputHTMLAttributes, ReactNode } from 'react'
import './LabeledInput.css'

type LabeledInputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  /** 'boxed' = bordered field like on login, 'underline' = just a bottom border like create-semester */
  variant?: 'boxed' | 'underline'
  rightSlot?: ReactNode
}

export default function LabeledInput({
  label,
  variant = 'boxed',
  rightSlot,
  className = '',
  ...rest
}: LabeledInputProps) {
  return (
    <div className="labeled-input">
      <div className="label-row">
        <label className="mono field-label">{label}</label>
        {rightSlot}
      </div>
      <input className={`mono-input ${variant === 'boxed' ? 'field-input' : 'field-underline'} ${className}`} {...rest} />
    </div>
  )
}
