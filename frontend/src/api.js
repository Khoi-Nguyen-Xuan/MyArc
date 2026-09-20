// Thin wrapper around the backend so components never build URLs by hand.
// One place to change if the API base moves (e.g. behind a proxy in prod).
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  listSemesters: () => request("/api/semesters"),
  createSemester: (name) =>
    request("/api/semesters", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    }),

  listCourses: (semesterId) => request(`/api/semesters/${semesterId}/courses`),
  createCourse: (semesterId, name, code) =>
    request(`/api/semesters/${semesterId}/courses`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, code }),
    }),

  listCourseUploads: (courseId) => request(`/api/courses/${courseId}/uploads`),
  uploadSyllabus: (courseId, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/api/courses/${courseId}/uploads`, {
      method: "POST",
      body: form,
    });
  },
};
