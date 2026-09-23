import { useState } from 'react'
import { Link } from 'react-router-dom'
import TopBar, { Logo, StepDots } from '../components/TopBar'
import WoodButton from '../components/WoodButton'
import CourseCard from '../components/CourseCard'
import UploadSlot from '../components/UploadSlot'
import './UploadSyllabi.css'

const initialCourses = [
  { code: 'CMPUT 301', title: 'Introduction to Software Engineering', status: 'deciphered' as const, fileName: 'CMPUT301_Syllabus.pdf' },
  { code: 'STAT 252', title: 'Introduction to Applied Statistics', status: 'deciphered' as const, fileName: 'STAT252_Outline.pdf' },
  { code: 'BIOL 207', title: 'Introductory Genetics', status: 'deciphering' as const, fileName: 'BIOL207_Syllabus_2026.pdf', progress: 64 },
  { code: 'ENGL 102', title: 'Critical Writing About Literature', status: 'empty' as const },
  { code: 'CMPUT 401', title: 'Capstone Project', status: 'deciphered' as const, fileName: 'CMPUT401_Capstone.pdf' },
]

export default function UploadSyllabi() {
  const [courses] = useState(initialCourses)

  const doneCount = courses.filter((c) => c.status === 'deciphered').length
  const progressPct = Math.round((doneCount / courses.length) * 100)

  return (
    <div className="bg-ambient">
      <TopBar
        left={
          <>
            <Link to="/create-semester" className="back-link">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#B7AC90" strokeWidth="2.2">
                <path d="M19 12H5M11 18l-6-6 6-6" />
              </svg>
              Back
            </Link>
            <Logo />
          </>
        }
        right={
          <>
            <span className="mono chapter-label">Chapter II — Trials &amp; Scrolls</span>
            <StepDots total={3} active={2} />
          </>
        }
      />

      <div className="upload-header">
        <div>
          <h1 className="upload-title">Deliver Your Syllabi</h1>
          <p className="upload-subtitle">
            Present a syllabus scroll for each course — dates, weights and rules are read automatically.
          </p>
        </div>
        <button className="btn-outline add-course-btn">+ Add Course</button>
      </div>

      <div className="upload-grid">
        {courses.map((course) => {
          if (course.status === 'empty') {
            return <UploadSlot key={course.code} code={course.code} title={course.title} />
          }
          if (course.status === 'deciphering') {
            return (
              <CourseCard
                key={course.code}
                status="deciphering"
                code={course.code}
                title={course.title}
                fileName={course.fileName}
                progress={course.progress}
              />
            )
          }
          return (
            <CourseCard
              key={course.code}
              status="deciphered"
              code={course.code}
              title={course.title}
              fileName={course.fileName}
            />
          )
        })}

        <div className="add-course-tile">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#B7AC90" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add Another Course
        </div>
      </div>

      <TopBar
        variant="bottom"
        left={
          <>
            <div className="progress-bar-small">
              <div className="progress-bar-small-fill" style={{ width: `${progressPct}%` }} />
            </div>
            <span className="mono progress-caption-small">{doneCount} / {courses.length} scrolls deciphered</span>
          </>
        }

        right={
          <WoodButton style={{ padding: '13px 24px', width: 'auto' }}>
            Begin the Reckoning
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#241D10" strokeWidth="2.6">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </WoodButton>
        }
      />
    </div>
  )
}
