import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const TOKEN_KEY = 'myarc_access_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export const api = axios.create({
  baseURL: API_BASE_URL,
})

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearToken()
    }
    return Promise.reject(error)
  },
)

// ---------------------------------------------------------------------------
// auth
// ---------------------------------------------------------------------------

export interface AuthResponse {
  success: boolean
  message: string
  accessToken?: string
}

export interface SimpleResponse {
  success: boolean
  message: string
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/login', { email, password })
  return data
}

export async function signup(email: string, password: string): Promise<SimpleResponse> {
  const { data } = await api.post<SimpleResponse>('/auth/signup', { email, password })
  return data
}

// ---------------------------------------------------------------------------
// courses
// ---------------------------------------------------------------------------

export interface AssessmentItem {
  type: string
  score_percent: number
  date: string
}

export interface EvidenceItem {
  link: string
  'content-summary': string
}

// key names match the backend's exact wire format (including the
// spaces/hyphens) — see backend app/schemas/course.py
export interface CourseResponse {
  id: number
  course_semester: string | null
  course_name: string | null
  professor_name: string | null
  course_code: string | null
  evaluate: AssessmentItem[]
  'short-review': string | null
  workload: number | null
  'conceptual difficult': number | null
  assessment_weighting: number | null
  'continious-study requirement': number | null
  'student-review difficulity': number | null
  evidence: EvidenceItem[]
  summary: string | null
  reasoning: string | null
  ranking: string | null
  point: number | null
  confidence: number | null
  // recommended study hours/week outside class (null for older courses)
  weekly_hours_min: number | null
  weekly_hours_max: number | null
}

export async function getCourses(): Promise<CourseResponse[]> {
  const { data } = await api.get<CourseResponse[]>('/courses/')
  return data
}

export async function getCourse(id: number): Promise<CourseResponse> {
  const { data } = await api.get<CourseResponse>(`/courses/${id}`)
  return data
}

export async function deleteCourse(id: number): Promise<void> {
  await api.delete(`/courses/${id}`)
}

// courseCode lets the backend start researching right away, in parallel with
// reading the syllabus; term is e.g. "Fall 2026"
export async function uploadSyllabus(file: File, courseCode: string, term: string): Promise<CourseResponse> {
  const formData = new FormData()
  formData.append('pdfFile', file)
  formData.append('course_code', courseCode)
  formData.append('term', term)
  const { data } = await api.post<CourseResponse>('/courses/upload-syllabus', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// ---------------------------------------------------------------------------
// dashboard
// ---------------------------------------------------------------------------

export interface CourseTestItem {
  course_name: string
  type: string
  score_percent: number
}

export interface DateEntry {
  date: string
  course_test: CourseTestItem[]
}

export interface WeekEntry {
  start_date: string
  end_date: string
  dates: DateEntry[]
}

export interface DashboardCurrentState {
  overload: string
  priority_course: string
  busiest_upcoming_week: string
  current_course_tracking: number
  undated_assessments: number // assessments with no date in the syllabus
  upcoming_weeks: WeekEntry[]
}

export async function getDashboardCurrentState(): Promise<DashboardCurrentState> {
  const { data } = await api.get<DashboardCurrentState>('/dashboard/current-state')
  return data
}
