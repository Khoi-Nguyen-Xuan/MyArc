import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Signup from './pages/Signup'
import CreateSemester from './pages/CreateSemester'
import UploadSyllabi from './pages/UploadSyllabi'
import Analyzing from './pages/Analyzing'
import Dashboard from './pages/Dashboard'

// 6 screens wired up now, more chapters coming later
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/create-semester" element={<CreateSemester />} />
        <Route path="/upload-syllabi" element={<UploadSyllabi />} />
        <Route path="/analyzing" element={<Analyzing />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
