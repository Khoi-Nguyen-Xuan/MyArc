import PanelDark from './PanelDark'
import './CourseCard.css'

type DecipheredCourseProps = {
  status: 'deciphered'
  code: string
  title: string
  fileName: string
  onReupload?: () => void
}

type DecipheringCourseProps = {
  status: 'deciphering'
  code: string
  title: string
  fileName: string
  progress: number // 0-100
}

type CourseCardProps = DecipheredCourseProps | DecipheringCourseProps

// a course tile that already has a syllabus attached: either done parsing or still parsing
export default function CourseCard(props: CourseCardProps) {
  const { code, title } = props

  return (
    <PanelDark className="course-card">
      <div className="course-card-top">
        <div>
          <div className="mono course-code">{code}</div>
          <div className="course-title">{title}</div>
        </div>

        {props.status === 'deciphered' && (
          <span className="mono status-done">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#1D2E0C" strokeWidth="3">
              <path d="M20 6L9 17l-5-5" />
            </svg>
            Deciphered
          </span>
        )}

        {props.status === 'deciphering' && (
          <span className="mono status-pending">Deciphering…</span>
        )}
      </div>

      {props.status === 'deciphered' && (
        <div className="file-row">
          <span className="mono file-name">{props.fileName}</span>
          <a href="#" className="reupload-link" onClick={props.onReupload}>Re-upload</a>
        </div>
      )}

      {props.status === 'deciphering' && (
        <div className="progress-block">
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${props.progress}%` }} />
          </div>
          <div className="mono progress-caption">{props.fileName} — {props.progress}%</div>
        </div>
      )}
    </PanelDark>
  )
}
