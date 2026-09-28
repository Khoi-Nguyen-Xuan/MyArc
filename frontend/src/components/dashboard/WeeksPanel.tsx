import GoldRule from '../../components/GoldRule'
import type { WeekLoad } from './types'
import './WeeksPanel.css'
import WoodenBoard from '../../components/WoodenBoard'

// green / yellow / red bands for the week's load (0-100)
// `text` is a darker shade for the label, so it stays readable on the light row
function loadLevel(load: number) {
  if (load >= 75) return { label: 'Heavy', color: '#d22623', text: '#b3261e' }
  if (load >= 50) return { label: 'Busy', color: '#e0a800', text: '#8a5a00' }
  return { label: 'Light', color: '#099d0e', text: '#0b7a10' }
}

function rowTitle(w: WeekLoad) {
  const real = w.weightPercent > 0 ? `${w.weightPercent}% of your grades due this week` : 'No dated deadlines this week'
  return w.estimated ? `${real} (bar is a placeholder estimate)` : real
}

export default function WeeksPanel({ weeks, undatedCount = 0 }: { weeks: WeekLoad[]; undatedCount?: number }) {
  const anyEstimated = weeks.some((w) => w.estimated)
  return (
    <WoodenBoard style={{ position: 'relative' }}>
      <div className="paper-header-bg">
        <div className="dash-panel-title ">Next Eight Weeks</div>
      </div>
      <GoldRule />
      <div className="weeks-list">
        {weeks.map((w) => {
          const level = loadLevel(w.load)
          return (
            <div key={w.label} className="weeks-row paper-bg" title={rowTitle(w)}>
              <span className="mono weeks-label">{w.label}</span>
              <div className="weeks-bar-track">
                <div className="weeks-bar-fill" style={{ width: `${w.load}%`, background: level.color }} />
              </div>
              <span className="mono weeks-hours" style={{ color: level.text, fontWeight: 600 }}>
                {level.label}
              </span>
            </div>
          )
        })}
      </div>

      <div className="mono weeks-legend">
        <span><i style={{ background: '#099d0e' }} /> Light</span>
        <span><i style={{ background: '#e0a800' }} /> Busy</span>
        <span><i style={{ background: '#d22623' }} /> Heavy</span>
      </div>
      {anyEstimated && (
        <p className="mono weeks-note">
          Estimated view — {undatedCount > 0 ? `${undatedCount} assessments have no dates yet, so ` : ''}
          weeks follow a typical semester pattern.
        </p>
      )}
      <a href="#" className="mono weeks-see-all gold-underline">
        See Full Calendar &rarr;
      </a>
    </WoodenBoard>
  )
}
