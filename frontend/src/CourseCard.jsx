import { useEffect, useState } from "react";
import { api } from "./api";

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function CourseCard({ course, onError }) {
  const [uploads, setUploads] = useState([]);
  const [uploading, setUploading] = useState(false);

  function refresh() {
    api.listCourseUploads(course.id).then(setUploads).catch((e) => onError(e.message));
  }

  useEffect(refresh, [course.id]);

  async function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await api.uploadSyllabus(course.id, file);
      refresh();
    } catch (err) {
      onError(err.message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  return (
    <div className="course-card">
      <h3>
        {course.name}
        {course.code && <span className="code"> ({course.code})</span>}
      </h3>

      <label className="upload-button">
        {uploading ? "Uploading..." : "Upload syllabus PDF"}
        <input type="file" accept="application/pdf" onChange={handleFileChange} disabled={uploading} hidden />
      </label>

      <ul className="history-trail">
        {uploads.map((u) => (
          <li key={u.id}>
            <span className="filename">{u.original_filename}</span>
            <span className="meta">
              {new Date(u.uploaded_at).toLocaleString()} - {formatBytes(u.size_bytes)} - {u.status}
            </span>
          </li>
        ))}
        {uploads.length === 0 && <li className="empty">No uploads yet.</li>}
      </ul>
    </div>
  );
}
