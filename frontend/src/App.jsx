import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import ModoSeleccion from './pages/ModoSeleccion'
import Practica from './pages/Practica'
import Historial from './pages/Historial'
import PanelDocente from './pages/PanelDocente'

const inicio = (user) => (user?.rol === 'docente' ? '/docente' : '/modos')

function PrivateRoute({ children }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" replace />
}

function DocenteRoute({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return user.rol === 'docente' ? children : <Navigate to="/modos" replace />
}

function PublicRoute({ children }) {
  const { user } = useAuth()
  return user ? <Navigate to={inicio(user)} replace /> : children
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/modos" element={<PrivateRoute><ModoSeleccion /></PrivateRoute>} />
          <Route path="/practica" element={<PrivateRoute><Practica /></PrivateRoute>} />
          <Route path="/historial" element={<PrivateRoute><Historial /></PrivateRoute>} />
          <Route path="/docente" element={<DocenteRoute><PanelDocente /></DocenteRoute>} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
