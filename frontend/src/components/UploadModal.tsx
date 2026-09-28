import { useEffect, useState } from 'react'
import type { ChangeEvent } from 'react'
import axios from 'axios'
import WoodButton from './WoodButton'
import PanelDark from './PanelDark'
import ParchmentCard from './ParchmentCard'
import { uploadSyllabus } from '../lib/api'
import type { CourseResponse } from '../lib/api'
import './UploadModal.css'

// stages we show while the upload request is in flight - the backend does
// this all in one call, so there's no real per-stage progress from the
// server. we just advance through these on a timer to give a sense of what
// is happening behind the scenes, and let the current one sit at "active"
// until the actual response comes back.
const UPLOAD_STAGES = ['Parsing syllabus', 'Searching for student reviews', 'Evaluating course'] as const

type StageStatus = 'done' | 'active' | 'pending'

export default function UploadModal({
  open,
  onClose,
  onUploaded,
}: {
  open: boolean
  onClose: () => void
  onUploaded: (course: CourseResponse) => void
}) {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // raw response from the backend, shown so we can check the pipeline output
  const [result, setResult] = useState<CourseResponse | null>(null)
  const [stageIndex, setStageIndex] = useState(0)

  // step through the fake stages while uploading is true
  useEffect(() => {
    if (!uploading) {
      setStageIndex(0)
      return
    }
    const id = setInterval(() => {
      setStageIndex((i) => Math.min(i + 1, UPLOAD_STAGES.length - 1))
    }, 2200)
    return () => clearInterval(id)
  }, [uploading])

  if (!open) return null

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    setFile(e.target.files?.[0] ?? null)
    setError(null)
  }

  async function handleUpload() {
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const course = await uploadSyllabus(file)
      onUploaded(course)
      setFile(null)
      setResult(course) // keep the modal open to show the JSON
    } catch (err) {
      // FastAPI puts the reason in `detail` (422 bad file, 503 missing API key, ...)
      const detail = axios.isAxiosError(err) ? err.response?.data?.detail : null
      setError(typeof detail === 'string' ? detail : 'Upload failed. Is the backend running?')
    } finally {
      setUploading(false)
    }
  }

  function handleClose() {
    if (uploading) return // don't allow closing mid-upload
    setFile(null)
    setError(null)
    setResult(null)
    onClose()
  }

  return (
    <div className="upload-modal-backdrop" onClick={handleClose}>
      <div
        className={`upload-modal-wrap${result ? ' upload-modal-wrap-result' : ''}`}
        onClick={(e) => e.stopPropagation()}
      >
        <PanelDark className="upload-modal-panel">
          <ParchmentCard style={{ padding: '36px 34px', overflowY: 'auto' }}>
            <h2 className="upload-modal-title">
              {uploading ? 'Deciphering Your Scroll' : 'Present a Syllabus Scroll'}
            </h2>
            <p className="upload-modal-subtitle">
              {uploading
                ? `${file?.name ?? 'Your syllabus'} is being read — this takes a moment.`
                : 'Upload a PDF or Word syllabus — dates, weights and rules are read automatically.'}
            </p>

            {!uploading && !result && (
              <label className="upload-modal-dropzone">
                <input
                  type="file"
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={handleFileChange}
                  hidden
                />
                <span className="mono">{file ? file.name : 'Click to choose a PDF or .docx'}</span>
              </label>
            )}

            {error && <p className="mono upload-modal-error">{error}</p>}

            {uploading && (
              <div className="upload-stage-list">
                {UPLOAD_STAGES.map((label, i) => (
                  <UploadStageRow
                    key={label}
                    label={label}
                    status={i < stageIndex ? 'done' : i === stageIndex ? 'active' : 'pending'}
                  />
                ))}
              </div>
            )}

            {result && (
              <pre className="mono upload-modal-json">
                {JSON.stringify(result, null, 2)}
              </pre>
            )}

            <div className="upload-modal-actions">
              <button className="btn-outline" onClick={handleClose} disabled={uploading}>
                {result ? 'Close' : 'Cancel'}
              </button>
              {!result && (
                <WoodButton onClick={handleUpload} disabled={!file || uploading}>
                  {uploading ? 'Working…' : 'Upload'}
                </WoodButton>
              )}
            </div>
          </ParchmentCard>
        </PanelDark>
      </div>
    </div>
  )
}

function UploadStageRow({ label, status }: { label: string; status: StageStatus }) {
  return (
    <div className={`mono upload-stage upload-stage-${status}`}>
      {status === 'done' && (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#1D2E0C" strokeWidth="3" className="upload-stage-icon">
          <path d="M20 6L9 17l-5-5" />
        </svg>
      )}
      {status === 'active' && (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#8A6B33" strokeWidth="2.5" className="upload-stage-icon upload-stage-spin">
          <circle cx="12" cy="12" r="9" opacity="0.3" />
          <path d="M12 3a9 9 0 0 1 9 9" />
        </svg>
      )}
      {status === 'pending' && <span className="upload-stage-box" />}
      {label}
    </div>
  )
}
