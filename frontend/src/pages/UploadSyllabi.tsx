import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import TopBar from '../components/TopBar'
import CourseCard from '../components/CourseCard'
import UploadModal from '../components/UploadModal'
import { getCourses, getToken } from '../lib/api'
import type { CourseResponse } from '../lib/api'
import './UploadSyllabi.css'

export default function UploadSyllabi() {
  const navigate = useNavigate()
  const [courses, setCourses] = useState<CourseResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)

  useEffect(() => {
    if (!getToken()) {
      navigate('/login')
      return
    }
    getCourses()
      .then(setCourses)
      .finally(() => setLoading(false))
  }, [navigate])

  function handleUploaded(course: CourseResponse) {
    setCourses((prev) => [course, ...prev])
  }

  return (
    <div className="bg-ambient">
      <TopBar />

      <div className="upload-header">
        <div>
          <h1 className="upload-title">Deliver Your Syllabi</h1>
          <p className="upload-subtitle">
            Present a syllabus scroll for each course — dates, weights and rules are read automatically.
          </p>
        </div>
        <button className="btn-outline add-course-btn" onClick={() => setModalOpen(true)}>
          + Add Course
        </button>
      </div>

      <div className="upload-grid">
        {loading && <p className="mono">Loading your syllabi…</p>}

        {!loading && courses.length === 0 && (
          <p className="mono">No syllabi uploaded yet — add your first course.</p>
        )}

        {courses.map((course) => (
          <CourseCard
            key={course.id}
            status="deciphered"
            code={course.course_code || `#${course.id}`}
            title={course.course_name || 'Untitled course'}
            fileName={course.professor_name || course.course_semester || 'Uploaded'}
          />
        ))}

        <div className="add-course-tile" onClick={() => setModalOpen(true)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#B7AC90" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add Another Course
        </div>
      </div>

      <UploadModal open={modalOpen} onClose={() => setModalOpen(false)} onUploaded={handleUploaded} />
    </div>
  )
}
