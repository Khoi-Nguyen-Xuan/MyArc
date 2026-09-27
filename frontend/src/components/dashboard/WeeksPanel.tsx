import GoldRule from '../../components/GoldRule'
import type { WeekLoad } from './types'
import './WeeksPanel.css'
import WoodenBoard from '../../components/WoodenBoard'

function loadColor(load: number) {
  if (load >= 75) return '#d22623' // High load: Bright Coral/Red
  if (load >= 50) return '#c87400' // Mid load:  Bright Warm Gold/Amber
  return '#099d0e'                 // Low load:  Bright Fresh Green
}
export default function WeeksPanel({ weeks }: { weeks: WeekLoad[] }) {
  return (
    // <PanelDark className="dash-panel dash-panel-weeks" showCorners={false}>
    <WoodenBoard style={{ position: 'relative' }}>
      <div className="paper-header-bg">
        <div className="dash-panel-title ">Next Eight Weeks</div>
      </div>
      <GoldRule />
      <div className="weeks-list">
        {weeks.map((w) => (
          <div key={w.label} className="weeks-row paper-bg">
            <span className="mono weeks-label">
              {/* {w.milestone && <span className="weeks-dot" />} */}
              {w.label}
            </span>
            <div className="weeks-bar-track">
              <div
                className="weeks-bar-fill"
                style={{ width: `${w.load}%`, background: loadColor(w.load) }}
              />
            </div>
            <span className="mono weeks-hours" style={{ color: loadColor(w.load) }}>
              {w.hours}h
            </span>
          </div>
        ))}
      </div>
      <a href="#" className="mono weeks-see-all gold-underline">
        See Full Calendar &rarr;
      </a>
    </WoodenBoard >
    // </PanelDark>
  )
}
