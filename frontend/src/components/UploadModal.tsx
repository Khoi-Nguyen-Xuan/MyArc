import { useState } from 'react'
import type { ChangeEvent } from 'react'
import WoodButton from './WoodButton'
import PanelDark from './PanelDark'
import ParchmentCard from './ParchmentCard'
import { uploadSyllabus } from '../lib/api'
import type { CourseResponse } from '../lib/api'
import './UploadModal.css'

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
      onClose()
    } catch {
      setError('Upload failed. Make sure the file is a PDF and try again.')
    } finally {
      setUploading(false)
    }
  }

  function handleClose() {
    if (uploading) return // don't allow closing mid-upload
    setFile(null)
    setError(null)
    onClose()
  }

  return (
    <div className="upload-modal-backdrop" onClick={handleClose}>
      <div className="upload-modal-wrap" onClick={(e) => e.stopPropagation()}>
        <PanelDark className="upload-modal-panel">
          <ParchmentCard style={{ padding: '36px 34px' }}>
            <h2 className="upload-modal-title">Present a Syllabus Scroll</h2>
            <p className="upload-modal-subtitle">
              Upload a PDF syllabus — dates, weights and rules are read automatically.
            </p>

            <label className="upload-modal-dropzone">
              <input type="file" accept="application/pdf" onChange={handleFileChange} hidden />
              <span className="mono">{file ? file.name : 'Click to choose a PDF'}</span>
            </label>

            {error && <p className="mono upload-modal-error">{error}</p>}
            {uploading && (
              <p className="mono upload-modal-status">Deciphering your syllabus, this may take a moment…</p>
            )}

            <div className="upload-modal-actions">
              <button className="btn-outline" onClick={handleClose} disabled={uploading}>
                Cancel
              </button>
              <WoodButton onClick={handleUpload} disabled={!file || uploading}>
                {uploading ? 'Uploading...' : 'Upload'}
              </WoodButton>
            </div>
          </ParchmentCard>
        </PanelDark>
      </div>
    </div>
  )
}
