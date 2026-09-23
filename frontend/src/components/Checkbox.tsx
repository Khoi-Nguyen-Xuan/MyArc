import './Checkbox.css'

export default function Checkbox({
  checked,
  onChange,
  label,
}: {
  checked: boolean
  onChange: (checked: boolean) => void
  label: string
}) {
  return (
    <div className="checkbox-row" onClick={() => onChange(!checked)}>
      <div className={`chk ${checked ? 'checked' : ''}`} />
      <span className="checkbox-label">{label}</span>
    </div>
  )
}
