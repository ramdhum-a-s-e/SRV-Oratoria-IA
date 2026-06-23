import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../api'

const C = { bg: '#0f172a', card: '#1e293b', border: '#334155', text: '#f1f5f9', muted: '#94a3b8', blue: '#6366f1', err: '#f87171' }

function Campo({ label, type = 'text', value, onChange, placeholder }) {
  return (
    <div style={{ marginBottom: '14px', textAlign: 'left' }}>
      <label style={{ display: 'block', fontSize: '13px', color: C.muted, marginBottom: '4px' }}>{label}</label>
      <input
        type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
        style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${C.border}`, backgroundColor: '#0f172a', color: C.text, fontSize: '15px', boxSizing: 'border-box' }}
      />
    </div>
  )
}

function validar(modo, form) {
  const soloLetras = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+$/
  const userOk     = /^[A-Za-z0-9._]+$/
  if (modo === 'register') {
    const nombre   = form.nombre.trim()
    const apellido = form.apellido.trim()
    if (nombre.length < 2 || nombre.length > 50) return 'El nombre debe tener entre 2 y 50 caracteres.'
    if (!soloLetras.test(nombre))   return 'El nombre solo puede contener letras (sin numeros).'
    if (apellido.length < 2 || apellido.length > 50) return 'El apellido debe tener entre 2 y 50 caracteres.'
    if (!soloLetras.test(apellido)) return 'El apellido solo puede contener letras (sin numeros).'
    if (form.grado.trim()   && !/^[A-Za-z0-9°º]{1,10}$/.test(form.grado.trim()))  return 'Grado invalido (ej. 1ro).'
    if (form.seccion.trim() && !/^[A-Za-z]{1,2}$/.test(form.seccion.trim()))      return 'Seccion invalida (1 o 2 letras, ej. A).'
  }
  const u = form.username.trim()
  if (u.length < 3 || u.length > 30) return 'El usuario debe tener entre 3 y 30 caracteres.'
  if (!userOk.test(u))               return 'El usuario solo puede contener letras, numeros, punto y guion bajo.'
  if (form.password.length < 6)      return 'La contrasena debe tener al menos 6 caracteres.'
  return null
}

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [modo, setModo] = useState('login')
  const [form, setForm] = useState({ nombre: '', apellido: '', username: '', password: '', grado: '', seccion: '' })
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  const set = k => v => setForm(f => ({ ...f, [k]: v }))

  const submit = async e => {
    e.preventDefault()
    const fallo = validar(modo, form)
    if (fallo) { setError(fallo); return }
    setCargando(true); setError('')
    try {
      const url = modo === 'login' ? '/auth/login' : '/auth/register'
      const body = modo === 'login'
        ? { username: form.username.trim(), password: form.password }
        : {
            nombre: form.nombre.trim(), apellido: form.apellido.trim(),
            username: form.username.trim(), password: form.password,
            grado: form.grado.trim() || null, seccion: form.seccion.trim() || null,
          }
      const res = await api.post(url, body)
      login(res.data.access_token, res.data.user)
      navigate('/modos')
    } catch (err) {
      const detail = err.response?.data?.detail
      const msg = Array.isArray(detail)
        ? detail.map(d => (d.msg || '').replace(/^Value error,?\s*/i, '')).join(' ')
        : detail
      setError(msg || 'Error al conectar con el servidor')
    } finally {
      setCargando(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: C.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ backgroundColor: C.card, border: `1px solid ${C.border}`, borderRadius: '16px', padding: '32px', width: '100%', maxWidth: '420px' }}>
        <h1 style={{ color: C.text, textAlign: 'center', margin: '0 0 4px', fontSize: '22px' }}>SRV - Oratoria</h1>
        <p style={{ color: C.muted, textAlign: 'center', margin: '0 0 24px', fontSize: '14px' }}>Sistema de Retroalimentacion por Voz</p>

        <div style={{ display: 'flex', borderRadius: '8px', overflow: 'hidden', border: `1px solid ${C.border}`, marginBottom: '24px' }}>
          {['login', 'register'].map(m => (
            <button key={m} onClick={() => { setModo(m); setError('') }}
              style={{ flex: 1, padding: '10px', border: 'none', cursor: 'pointer', fontWeight: 'bold', fontSize: '14px', backgroundColor: modo === m ? C.blue : 'transparent', color: modo === m ? 'white' : C.muted }}>
              {m === 'login' ? 'Iniciar sesion' : 'Registrarse'}
            </button>
          ))}
        </div>

        <form onSubmit={submit}>
          {modo === 'register' && (
            <>
              <div style={{ display: 'flex', gap: '10px' }}>
                <div style={{ flex: 1 }}><Campo label="Nombre" value={form.nombre} onChange={set('nombre')} /></div>
                <div style={{ flex: 1 }}><Campo label="Apellido" value={form.apellido} onChange={set('apellido')} /></div>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <div style={{ flex: 1 }}><Campo label="Grado" value={form.grado} onChange={set('grado')} placeholder="1ro" /></div>
                <div style={{ flex: 1 }}><Campo label="Seccion" value={form.seccion} onChange={set('seccion')} placeholder="A" /></div>
              </div>
            </>
          )}
          <Campo label="Usuario" value={form.username} onChange={set('username')} placeholder="mi.usuario" />
          <Campo label="Contrasena" type="password" value={form.password} onChange={set('password')} />

          {error && <p style={{ color: C.err, fontSize: '13px', margin: '0 0 12px' }}>{error}</p>}

          <button type="submit" disabled={cargando}
            style={{ width: '100%', padding: '12px', borderRadius: '8px', border: 'none', backgroundColor: C.blue, color: 'white', fontWeight: 'bold', fontSize: '16px', cursor: cargando ? 'not-allowed' : 'pointer', opacity: cargando ? 0.7 : 1 }}>
            {cargando ? 'Cargando...' : modo === 'login' ? 'Entrar' : 'Crear cuenta'}
          </button>
        </form>
      </div>
    </div>
  )
}
