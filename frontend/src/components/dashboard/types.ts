// shared types for the dashboard - real data will come from the scoring
// pipeline (see Analyzing.tsx), this file just pins the shape down

export type Tier = 'S' | 'A' | 'B' | 'C' | 'D'

export type CourseRank = {
  code: string
  title: string
  tier: Tier
  hoursPerWeek: number
  confidence: number // 0-100
  crammable: boolean
}

export type WeekLoad = {
  label: string
  load: number // 0-100, drives the color band
  hours: number // hours of work that week, shown on the right
  milestone?: boolean // true = has a notable deadline that week (shows a dot)
}

export type QuestKind = 'exam' | 'assignment' | 'project'

export type QuestItem = {
  course: string
  title: string
  due: string
  kind: QuestKind
}
