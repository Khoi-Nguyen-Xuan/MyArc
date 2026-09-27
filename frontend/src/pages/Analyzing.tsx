import { useEffect, useState } from 'react'
import PanelDark from '../components/PanelDark'
import ParchmentCard from '../components/ParchmentCard'
import './Analyzing.css'
import TopBar from '../components/TopBar'

// checklist steps shown while the semester is being scored - first two are
// already done, one is in progress, the rest are queued
type StepStatus = 'done' | 'active' | 'pending'

const steps: { label: string; status: StepStatus }[] = [
  { label: 'Reading the scrolls — 5 / 5', status: 'done' },
  { label: 'Marking trials & deadlines', status: 'done' },
  { label: 'Gathering rumors — taverns, guild halls, past scholars', status: 'active' },
  { label: 'Weighing hardship & toil', status: 'pending' },
  { label: "Verifying the rumors — critic's pass", status: 'pending' },
  { label: 'Sealing the ranks & raising your dashboard', status: 'pending' },
]

// each course as it gets picked up by the scoring pipeline
type PickSlot = {
  code: string
  state: 'done' | 'active' | 'queued'
  progress: number // 0-100
}

const pickOrder: PickSlot[] = [
  { code: 'CMPUT301', state: 'done', progress: 100 },
  { code: 'STAT252', state: 'done', progress: 100 },
  { code: 'BIOL207', state: 'active', progress: 64 },
  { code: 'ENGL102', state: 'queued', progress: 20 },
  { code: 'CMPUT401', state: 'queued', progress: 88 },
]

export default function Analyzing() {
  // fake progress bump so the page doesn't look static - real version will
  // swap this for a websocket / poll against the scoring job
  const [tick, setTick] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1500)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="bg-ambient ">
      <TopBar />

      <div className="analyzing-center">
        <div className="analyzing-content">
          <svg width="60" height="60" viewBox="0 0 24 24" fill="none" className="analyzing-spinner">
            <circle cx="12" cy="12" r="9" stroke="#3A342A" strokeWidth="2.5" />
            <path d="M12 3a9 9 0 0 1 9 9" stroke="#8A7245" strokeWidth="2.5" strokeLinecap="round" />
          </svg>

          <h1 className="analyzing-title">The Reckoning Is Underway</h1>
          <p className="analyzing-subtitle">
            Your scrolls are read, the realm&rsquo;s rumors gathered, and each trial&rsquo;s weight is being measured.
          </p>

          <ParchmentCard style={{ width: '100%', maxWidth: '1000px', textAlign: 'left', height: '230px', padding: '26px 30px', marginBottom: 22, position: 'relative' }}>
            {steps.map((step) => (
              <ChecklistRow key={step.label} label={step.label} status={step.status} />
            ))}
          </ParchmentCard>

          <div className="gold-underline pick-order-label mono">Pick Order — Trials Being Chosen</div>

          <div className="pick-row">
            {pickOrder.map((slot, i) => (
              <PickTile key={slot.code} slot={slot} index={i + 1} />
            ))}
          </div>

          <p className="mono analyzing-footnote">
            Usually 30–60 seconds. You shall arrive straight at your dashboard.
            {tick > 20 && ' Almost there…'}
          </p>
        </div>
      </div>
    </div>
  )
}

function ChecklistRow({ label, status }: { label: string; status: StepStatus }) {
  return (
    <div className={`mono checklist-row checklist-${status}`}>
      {status === 'done' && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#1D2E0C" strokeWidth="3">
          <path d="M20 6L9 17l-5-5" />
        </svg>
      )}
      {status === 'active' && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#423212" strokeWidth="2.5">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 2" />
        </svg>
      )}
      {status === 'pending' && <span className="checklist-box" />}
      {label}
    </div>
  )
}

function PickTile({ slot, index }: { slot: PickSlot; index: number }) {
  return (
    <PanelDark className={`pick-slot pick-slot-${slot.state}`} showCorners={false}>
      <div className="mono pick-index">{String(index).padStart(2, '0')}</div>
      {slot.state === 'done' && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#1D2E0C" strokeWidth="3" className="pick-icon">
          <path d="M20 6L9 17l-5-5" />
        </svg>
      )}
      {slot.state === 'active' && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#423212" strokeWidth="2.5" className="pick-icon">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 2" />
        </svg>
      )}
      {slot.state === 'queued' && (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#453522" strokeWidth="2" className="pick-icon">
          <circle cx="12" cy="12" r="9" />
        </svg>
      )}
      <div className="mono pick-code">{slot.code}</div>
      <div className="pick-progress-track">
        <div
          className="pick-progress-fill"
          style={{ width: `${slot.progress}%`, background: slot.state === 'done' ? '#1D2E0C' : '#423212' }}
        />
      </div>
      <div className="mono pick-caption">{slot.state === 'done' ? 'Picked' : `${slot.progress}%`}</div>
    </PanelDark>
  )
}
