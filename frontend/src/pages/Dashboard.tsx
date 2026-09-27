import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AlertBar from '~/components/dashboard/AlertBar'
import RanksPanel from '~/components/dashboard/RanksPanel'
import WeeksPanel from '~/components/dashboard/WeeksPanel'
import type { CourseRank, WeekLoad, Tier } from '~/components/dashboard/types'
import './Dashboard.css'
import TopBar from '~/components/TopBar'
import { getCourses, getDashboardCurrentState, getToken } from '~/lib/api'
import type { CourseResponse, DashboardCurrentState } from '~/lib/api'

const VALID_TIERS: Tier[] = ['S', 'A', 'B', 'C', 'D']

function toCourseRank(course: CourseResponse): CourseRank | null {
  // ranking is only set once the real analysis pipeline runs (still a
  // placeholder stub server-side right now) - skip courses without one
  // rather than inventing a fake tier for them
  if (!course.ranking || !VALID_TIERS.includes(course.ranking as Tier)) return null

  return {
    code: course.course_code || `#${course.id}`,
    title: course.course_name || 'Untitled course',
    tier: course.ranking as Tier,
    // NOTE: backend's "workload" is a 0-10 difficulty score, not literal
    // hours/week - reused here as a placeholder until the pipeline
    // computes a real weekly-hours estimate
    hoursPerWeek: course.workload ?? 0,
    confidence: Math.round((course.confidence ?? 0) * 10), // backend is 0-10, UI wants 0-100
    // heuristic: a low continuous-study-requirement score means it can be
    // crammed closer to the exam - not a field the backend exposes directly
    crammable: (course['continious-study requirement'] ?? 10) < 5,
  }
}

function formatWeekLabel(isoDate: string) {
  return new Date(isoDate).toLocaleDateString('en-US', { month: 'short', day: '2-digit' })
}

function toWeekLoads(state: DashboardCurrentState): WeekLoad[] {
  return state.upcoming_weeks.map((week) => {
    const testCount = week.dates.reduce((sum, d) => sum + d.course_test.length, 0)
    const hasHeavyItem = week.dates.some((d) =>
      d.course_test.some((t) => ['midterm', 'exam', 'final'].includes(t.type.toLowerCase())),
    )
    return {
      label: formatWeekLabel(week.start_date),
      // NOTE: the backend doesn't compute a load % or hours estimate per
      // week yet - this is a rough client-side placeholder based on how
      // many assessments land in the week, not real workload data
      load: Math.min(100, testCount * 25),
      hours: testCount * 3,
      milestone: hasHeavyItem,
    }
  })
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [courses, setCourses] = useState<CourseResponse[]>([])
  const [state, setState] = useState<DashboardCurrentState | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!getToken()) {
      navigate('/login')
      return
    }
    Promise.all([getCourses(), getDashboardCurrentState()])
      .then(([c, s]) => {
        setCourses(c)
        setState(s)
      })
      .finally(() => setLoading(false))
  }, [navigate])

  if (loading) {
    return (
      <div className="bg-ambient">
        <TopBar />
        <p className="mono" style={{ padding: 40 }}>Loading your dashboard…</p>
      </div>
    )
  }

  const courseRanks = courses.map(toCourseRank).filter((c): c is CourseRank => c !== null)
  const weekLoads = state ? toWeekLoads(state) : []

  return (
    <div className="bg-ambient">
      <div className="dashboard-page">
        <TopBar />

        {state && state.priority_course && (
          <AlertBar
            courseCode={state.priority_course}
            courseTitle={`${state.overload} load`}
            message={`Busiest week: ${state.busiest_upcoming_week || 'N/A'}`}
          />
        )}

        <div className="dash-grid">
          <RanksPanel courses={courseRanks} />
          <WeeksPanel weeks={weekLoads} />
        </div>
      </div>
    </div>
  )
}
