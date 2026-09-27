import GoldRule from '../../components/GoldRule'
import type { CourseRank, Tier } from './types'
import './RanksPanel.css'
import ParchmentCard from '../../components/ParchmentCard'
import ParchmentBorder from '../../components/ParchmentBorder'

const tierColor: Record<Tier, string> = {
  S: '#C9A96E',
  A: '#8A9E5E',
  B: '#7A8FA0',
  C: '#A08A5E',
  D: '#A0605E',
}

export default function RanksPanel({ courses }: { courses: CourseRank[] }) {
  return (
    // <PanelDark className="dash-panel dash-panel-ranks" showCorners={false}>
    <div style={{ position: 'relative', display: 'flex', justifyContent: 'center', alignItems: 'center' }} >
      <ParchmentCard>
        <ParchmentBorder />
        <div className="parchment-content">

          <div className="dash-panel-title">Ranks of the Realm</div>
          <GoldRule />
          <div className="ranks-table">
            <div className="ranks-header mono">
              <span>Tier</span>
              <span>Course</span>
              <span>Hrs / Week</span>
              <span>Confidence</span>
              <span>Cram-Friendly</span>
            </div>
            {courses.map((c) => (
              <div key={c.code} className="ranks-row">
                <span
                  className="tier-badge"
                  style={{
                    borderColor: '#1B170E',
                    color: '#1B170E',
                    backgroundColor: tierColor[c.tier]
                  }}
                >
                  {c.tier}
                </span>
                <span className="ranks-course">
                  <span className="ranks-code mono">{c.code}</span>
                  <span className="ranks-title">{c.title}</span>
                </span>
                <span className="mono">{c.hoursPerWeek}h</span>
                <span className="mono">{c.confidence}%</span>
                <span className="mono">{c.crammable ? 'Yes' : 'No'}</span>
              </div>
            ))}
          </div>
        </div>
      </ParchmentCard>
    </div>
    // </PanelDark>
  )
}
