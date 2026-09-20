import { useEffect, useState } from "react";
import { api } from "./api";
import CourseCard from "./CourseCard.jsx";


export default function App() {
  const [semesters, setSemesters] = useState([]);
  const [selectedSemesterId, setSelectedSemesterId] = useState(null);
  const [newSemesterName, setNewSemesterName] = useState("");
  const [courses, setCourses] = useState([]);
  const [newCourseName, setNewCourseName] = useState("");
  const [newCourseCode, setNewCourseCode] = useState("");
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listSemesters().then(setSemesters).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!selectedSemesterId) {
      setCourses([]);
      return;
    }
    api
      .listCourses(selectedSemesterId)
      .then(setCourses)
      .catch((e) => setError(e.message));
  }, [selectedSemesterId]);

  async function handleCreateSemester(e) {
    e.preventDefault();
    if (!newSemesterName.trim()) return;
    try {
      const semester = await api.createSemester(newSemesterName.trim());
      setSemesters((prev) => [semester, ...prev]);
      setSelectedSemesterId(semester.id);
      setNewSemesterName("");
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleCreateCourse(e) {
    e.preventDefault();
    if (!newCourseName.trim() || !selectedSemesterId) return;
    try {
      const course = await api.createCourse(
        selectedSemesterId,
        newCourseName.trim(),
        newCourseCode.trim() || null
      );
      setCourses((prev) => [...prev, course]);
      setNewCourseName("");
      setNewCourseCode("");
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="page">
      <header>
        <h1>MyArc</h1>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="panel">
        <h2>1. Semester</h2>
        <div className="row">
          <select
            value={selectedSemesterId ?? ""}
            onChange={(e) => setSelectedSemesterId(Number(e.target.value) || null)}
          >
            <option value="">-- select a semester --</option>
            {semesters.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <form className="inline-form" onSubmit={handleCreateSemester}>
            <input
              placeholder="e.g. Fall 2026"
              value={newSemesterName}
              onChange={(e) => setNewSemesterName(e.target.value)}
            />
            <button type="submit">+ New semester</button>
          </form>
        </div>
      </section>

      {selectedSemesterId && (
        <section className="panel">
          <h2>2. Courses</h2>
          <form className="inline-form" onSubmit={handleCreateCourse}>
            <input
              placeholder="Course name (e.g. Linear Algebra)"
              value={newCourseName}
              onChange={(e) => setNewCourseName(e.target.value)}
            />
            <input
              placeholder="Code (e.g. MATH225)"
              value={newCourseCode}
              onChange={(e) => setNewCourseCode(e.target.value)}
            />
            <button type="submit">+ Add course</button>
          </form>

          <div className="course-grid">
            {courses.map((course) => (
              <CourseCard key={course.id} course={course} onError={setError} />
            ))}
            {courses.length === 0 && <p className="empty">No courses yet for this semester.</p>}
          </div>
        </section>
      )}
    </div>
  );
}
