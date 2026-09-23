import './GoldRule.css'

export default function GoldRule({ label }: { label?: string }) {
  return (
    <div className="gold-rule">
      <span className="ln" />
      {label && <span className="mono label">{label}</span>}
      <span className="ln" />
    </div>
  )
}
