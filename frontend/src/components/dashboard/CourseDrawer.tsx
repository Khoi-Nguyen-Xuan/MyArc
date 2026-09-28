import { useEffect } from 'react'
import type { CourseResponse } from '~/lib/api'
import './CourseDrawer.css'

// One criterion line from the backend's `reasoning` text
type CriterionReason = { name: string; score: number; text: string }

const CRITERION_LINE = /^(.+?) \(([\d.]+)\/10\): (.*)$/

function parseReasoning(reasoning: string | null) {
  const criteria: CriterionReason[] = []
  const other: string[] = []
  for (const line of (reasoning ?? '').split('\n')) {
    const trimmed = line.trim()
    if (!trimmed || trimmed === 'Notes:') continue
    const match = CRITERION_LINE.exec(trimmed)
    if (match) criteria.push({ name: match[1], score: Number(match[2]), text: match[3] })
    else other.push(trimmed.replace(/^- /, ''))
  }
  return { criteria, other }
}

function scoreColor(score: number) {
  if (score >= 7) return '#b3261e' // hard
  if (score >= 4) return '#a86b00' // moderate
  return '#2e7d32' // light
}

function sourceLabel(link: string | null) {
  if (!link) return 'Syllabus'
  try {
    const host = new URL(link).hostname.replace(/^www\./, '')
    return host.includes('reddit') ? 'Reddit' : host
  } catch {
    return 'Web'
  }
}

export default function CourseDrawer({ course, onClose }: { course: CourseResponse | null; onClose: () => void }) {
  // close on Escape
  useEffect(() => {
    if (!course) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [course, onClose])

  if (!course) return null

  const { criteria, other } = parseReasoning(course.reasoning)
  const point100 = course.point != null ? Math.round(course.point * 10) : null
  const confidence100 = course.confidence != null ? Math.round(course.confidence * 10) : null

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside
        className="bg-parchment course-drawer"
        role="dialog"
        aria-modal="true"
        aria-label={`Why ${course.course_code ?? 'this course'} is ranked ${course.ranking ?? ''}`}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="drawer-header">
          <span className="drawer-tier">{course.ranking ?? '?'}</span>
          <div className="drawer-heading">
            <div className="mono drawer-code">{course.course_code}</div>
            <h2 className="drawer-title">{course.course_name || 'Untitled course'}</h2>
          </div>
          <button type="button" className="drawer-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>

        <div className="mono drawer-stats">
          {point100 != null && <span>Difficulty {point100}/100</span>}
          {confidence100 != null && <span>Confidence {confidence100}%</span>}
          {course.weekly_hours_min != null && course.weekly_hours_max != null && (
            <span>
              {course.weekly_hours_min}–{course.weekly_hours_max}h / week
            </span>
          )}
        </div>

        {course['short-review'] && <p className="drawer-review">“{course['short-review']}”</p>}

        {course.summary && (
          <section>
            <h3 className="drawer-section-title">Why this rank</h3>
            <p className="drawer-text">{course.summary}</p>
          </section>
        )}

        {criteria.length > 0 && (
          <section>
            <h3 className="drawer-section-title">Difficulty breakdown</h3>
            {criteria.map((c) => (
              <div key={c.name} className="drawer-criterion">
                <div className="drawer-criterion-top">
                  <span className="drawer-criterion-name">{c.name}</span>
                  <span className="mono" style={{ color: scoreColor(c.score) }}>
                    {c.score}/10
                  </span>
                </div>
                <div className="drawer-bar-track">
                  <div
                    className="drawer-bar-fill"
                    style={{ width: `${c.score * 10}%`, background: scoreColor(c.score) }}
                  />
                </div>
                <p className="drawer-text drawer-criterion-text">{c.text}</p>
              </div>
            ))}
          </section>
        )}

        {course.evidence.length > 0 && (
          <section>
            <h3 className="drawer-section-title">Evidence ({course.evidence.length})</h3>
            <ul className="drawer-evidence">
              {course.evidence.map((item, i) => (
                <li key={i}>
                  <span className="mono drawer-source">{sourceLabel(item.link)}</span>
                  {item.link ? (
                    <a href={item.link} target="_blank" rel="noreferrer">
                      {item['content-summary']}
                    </a>
                  ) : (
                    <span>{item['content-summary']}</span>
                  )}
                </li>
              ))}
            </ul>
          </section>
        )}

        {other.length > 0 && (
          <section>
            <h3 className="drawer-section-title">Notes</h3>
            <ul className="drawer-notes">
              {other.map((line, i) => (
                <li key={i}>{line}</li>
              ))}
            </ul>
          </section>
        )}
      </aside>
    </div>
  )
}
