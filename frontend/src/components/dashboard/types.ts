// shared types for the dashboard - real data will come from the scoring
// pipeline (see Analyzing.tsx), this file just pins the shape down

export type Tier = 'S' | 'A' | 'B' | 'C' | 'D'

export type CourseRank = {
  id: number // backend course id, used to open the "Why?" drawer
  code: string
  title: string
  tier: Tier
  hoursLabel: string // e.g. "6–9h", or "—" when unknown
  confidence: number // 0-100
  crammable: boolean
}

export type WeekLoad = {
  label: string
  load: number // 0-100, drives the color band
  weightPercent: number // % of final grades due that week (real data only)
  estimated: boolean // true = load comes from the placeholder pattern, not real deadlines
  milestone?: boolean // true = has a notable deadline that week (shows a dot)
}

export type QuestKind = 'exam' | 'assignment' | 'project'

export type QuestItem = {
  course: string
  title: string
  due: string
  kind: QuestKind
}
