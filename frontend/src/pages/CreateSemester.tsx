import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import TopBar, { Logo, StepDots } from '../components/TopBar'
import PanelDark from '../components/PanelDark'
import ParchmentCard from '../components/ParchmentCard'
import WoodButton from '../components/WoodButton'
import LabeledInput from '../components/LabeledInput'
import './CreateSemester.css'

export default function CreateSemester() {
  const navigate = useNavigate()
  const [name, setName] = useState('Fall 2026')
  const [term, setTerm] = useState('Fall')
  const [year, setYear] = useState('2026')
  const [startDate, setStartDate] = useState('Sep 2, 2026')
  const [endDate, setEndDate] = useState('Dec 12, 2026')

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    navigate('/upload-syllabi')
  }

  return (
    <div className="bg-ambient">
      <TopBar
        left={<Logo />}
        right={
          <>
            <span className="mono chapter-label">Chapter I — Semester</span>
            <StepDots total={3} active={1} />
          </>
        }
      />

      <div className="create-center">
        <div className="create-card-wrap">
          <WoodButton tag className="create-tag">New Semester</WoodButton>

          <PanelDark variant="light" className="create-panel">
            <ParchmentCard style={{ padding: '54px 46px 42px 46px' }}>
              <h1 className="create-title">Chronicle a New Semester</h1>
              <p className="create-subtitle">
                Name your term and set its span — your four to six trials await on the next page.
              </p>

              <form className="create-form" onSubmit={handleSubmit}>
                <LabeledInput
                  label="Semester name"
                  variant="underline"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />

                <div className="create-row">
                  <LabeledInput
                    label="Term"
                    variant="underline"
                    value={term}
                    onChange={(e) => setTerm(e.target.value)}
                  />
                  <LabeledInput
                    label="Year"
                    variant="underline"
                    value={year}
                    onChange={(e) => setYear(e.target.value)}
                  />
                </div>

                <div className="create-row">
                  <LabeledInput
                    label="Start date"
                    variant="underline"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                  <LabeledInput
                    label="End date"
                    variant="underline"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>

                <div className="create-actions">
                  <a href="/login" className="cancel-link">Cancel</a>
                  <WoodButton type="submit" style={{ padding: '13px 26px', width: 'auto' }}>
                    Onward
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#241D10" strokeWidth="2.6">
                      <path d="M5 12h14M13 6l6 6-6 6" />
                    </svg>
                  </WoodButton>
                </div>
              </form>
            </ParchmentCard>
          </PanelDark>
        </div>
      </div>

      <div className="mono footer-note">You may add, remove or amend courses at any time.</div>
    </div>
  )
}
