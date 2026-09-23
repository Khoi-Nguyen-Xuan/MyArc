import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import CreateSemester from './pages/CreateSemester'
import UploadSyllabi from './pages/UploadSyllabi'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/create-semester" element={<CreateSemester />} />
        <Route path="/upload-syllabi" element={<UploadSyllabi />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
