import './UploadSlot.css'

// a course that's been added but has no syllabus yet - dashed drop zone
export default function UploadSlot({
  code,
  title,
  onUpload,
}: {
  code: string
  title: string
  onUpload?: () => void
}) {
  return (
    <div className="upload-slot">
      <div>
        <div className="mono upload-slot-code">{code}</div>
        <div className="upload-slot-title">{title}</div>
      </div>
      <div className="drop-zone" onClick={onUpload}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#B7AC90" strokeWidth="2">
          <path d="M12 16V4M7 9l5-5 5 5M4 20h16" />
        </svg>
        <span className="drop-zone-text">Present a syllabus scroll here, or click to upload</span>
      </div>
    </div>
  )
}
