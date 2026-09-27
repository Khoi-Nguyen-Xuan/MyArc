import './AlertBar.css'

type AlertBarProps = {
  courseCode: string
  courseTitle: string
  message: string
}

export default function AlertBar({ courseCode, courseTitle, message }: AlertBarProps) {
  return (
    <div className="dash-alert-bar">
      <img className="dash-alert-bg-left" src="/assets/left-metal.png" alt="Alert Background" />
      <img className="dash-alert-bg-right" src="/assets/left-metal.png" alt="Alert Background" />
      <div className="dash-alert-bg">
        <div className="dash-alert-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F1DDBE" strokeWidth="2">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 7v5l3 2" />
          </svg>
        </div>
        <div className="dash-alert-text">
          <div className="dash-alert-title">Priority This Week: {courseCode}</div>
          <div className="dash-alert-sub mono">
            {courseTitle} — {message}
          </div>
        </div>
        <div className="dash-alert-action-bg">
          <div className="dash-alert-action mono">View Quest &rarr;</div>
        </div>
      </div>
    </div>
  )
}
