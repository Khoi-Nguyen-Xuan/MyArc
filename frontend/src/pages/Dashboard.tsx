import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AlertBar from '~/components/dashboard/AlertBar'
import RanksPanel from '~/components/dashboard/RanksPanel'
import WeeksPanel from '~/components/dashboard/WeeksPanel'
import CourseDrawer from '~/components/dashboard/CourseDrawer'
import type { CourseRank, WeekLoad, Tier } from '~/components/dashboard/types'
import './Dashboard.css'
import TopBar from '~/components/TopBar'
import { getCourses, getDashboardCurrentState, getToken } from '~/lib/api'
import type { CourseResponse, DashboardCurrentState } from '~/lib/api'

const VALID_TIERS: Tier[] = ['S', 'A', 'B', 'C', 'D']

function toCourseRank(course: CourseResponse): CourseRank | null {
  // ranking is only set once the real analysis pipeline runs
  if (!course.ranking || !VALID_TIERS.includes(course.ranking as Tier)) return null

  return {
    id: course.id,
    code: course.course_code || `#${course.id}`,
    title: course.course_name || 'Untitled course',
    tier: course.ranking as Tier,
    hoursLabel: formatHours(course.weekly_hours_min, course.weekly_hours_max),
    confidence: Math.round((course.confidence ?? 0) * 10), // backend is 0-10, UI wants 0-100
    // heuristic: a low continuous-study-requirement score means it can be
    // crammed closer to the exam - not a field the backend exposes directly
    crammable: (course['continious-study requirement'] ?? 10) < 5,
  }
}

function formatHours(min: number | null, max: number | null) {
  if (min == null || max == null) return '—'
  return min === max ? `${min}h` : `${min}–${max}h`
}

function formatWeekLabel(isoDate: string) {
  const [y, m, d] = isoDate.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-US', { month: 'short', day: '2-digit' })
}

// PLACEHOLDER until deadline dates are extracted reliably (most assessments
// come back undated): a typical-semester load curve
const USE_PLACEHOLDER_WEEKS = true
const PLACEHOLDER_LOADS = [35, 45, 60, 80, 55, 40, 70, 90]

function toWeekLoads(state: DashboardCurrentState): WeekLoad[] {
  return state.upcoming_weeks.map((week, index) => {
    // share of final grades due this week, across all courses (0.25 = 25%)
    const weight = week.dates.reduce(
      (sum, d) => sum + d.course_test.reduce((s, t) => s + t.score_percent, 0),
      0,
    )
    const hasHeavyItem = week.dates.some((d) =>
      d.course_test.some((t) => ['midterm', 'exam', 'final'].includes(t.type.toLowerCase())),
    )
    // real load: 25% of grades due in one week fills the bar
    const realLoad = Math.min(100, Math.round(weight * 400))
    const placeholder = USE_PLACEHOLDER_WEEKS ? PLACEHOLDER_LOADS[index % PLACEHOLDER_LOADS.length] : 0
    return {
      label: formatWeekLabel(week.start_date),
      load: Math.max(realLoad, placeholder),
      weightPercent: Math.round(weight * 100),
      estimated: placeholder > realLoad,
      milestone: hasHeavyItem,
    }
  })
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [courses, setCourses] = useState<CourseResponse[]>([])
  const [state, setState] = useState<DashboardCurrentState | null>(null)
  const [loading, setLoading] = useState(true)
  const [whyCourseId, setWhyCourseId] = useState<number | null>(null)

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
          <RanksPanel courses={courseRanks} onWhy={setWhyCourseId} />
          <WeeksPanel weeks={weekLoads} undatedCount={state?.undated_assessments ?? 0} />
        </div>
      </div>

      <CourseDrawer
        course={courses.find((c) => c.id === whyCourseId) ?? null}
        onClose={() => setWhyCourseId(null)}
      />
    </div>
  )
}
