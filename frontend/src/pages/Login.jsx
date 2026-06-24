import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../api'
import { T } from '../ui/theme'
import { Pantalla, Lorito, Tarjeta, Campo, Boton } from '../ui/kit'

function validar(modo, form) {
  const soloLetras = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+$/
  const userOk     = /^[A-Za-z0-9._]+$/
  if (modo === 'register') {
    const nombre   = form.nombre.trim()
    const apellido = form.apellido.trim()
    if (nombre.length < 2 || nombre.length > 50) return 'El nombre debe tener entre 2 y 50 letras.'
    if (!soloLetras.test(nombre))   return 'El nombre solo puede tener letras (sin numeros).'
    if (apellido.length < 2 || apellido.length > 50) return 'El apellido debe tener entre 2 y 50 letras.'
    if (!soloLetras.test(apellido)) return 'El apellido solo puede tener letras (sin numeros).'
    if (form.grado.trim()   && !/^[A-Za-z0-9°º]{1,10}$/.test(form.grado.trim())) return 'Grado invalido (ej. 1ro).'
    if (form.seccion.trim() && !/^[A-Za-z]{1,2}$/.test(form.seccion.trim()))     return 'Seccion invalida (1 o 2 letras, ej. A).'
  }
  const u = form.username.trim()
  if (u.length < 3 || u.length > 30) return 'El usuario debe tener entre 3 y 30 caracteres.'
  if (!userOk.test(u))               return 'El usuario solo puede tener letras, numeros, punto y guion bajo.'
  if (form.password.length < 6)      return 'La contrasena debe tener al menos 6 caracteres.'
  return null
}

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [modo, setModo] = useState('login')
  const [form, setForm] = useState({ nombre: '', apellido: '', username: '', password: '', grado: '', seccion: '', rol: 'alumno' })
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
            username: form.username.trim(), password: form.password, rol: form.rol,
            grado: form.grado.trim() || null, seccion: form.seccion.trim() || null,
          }
      const res = await api.post(url, body)
      login(res.data.access_token, res.data.user)
      navigate(res.data.user.rol === 'docente' ? '/docente' : '/modos')
    } catch (err) {
      const detail = err.response?.data?.detail
      const msg = Array.isArray(detail)
        ? detail.map(d => (d.msg || '').replace(/^Value error,?\s*/i, '')).join(' ')
        : detail
      setError(msg || 'No pudimos conectar. Intenta de nuevo.')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Pantalla>
      <Lorito mensaje={modo === 'login' ? '¡Hola! Vamos a practicar' : '¡Crea tu cuenta!'} />

      <Tarjeta>
        {/* Pestañas grandes */}
        <div style={{ display: 'flex', gap: 8, background: '#f4eede', borderRadius: 999, padding: 5, marginBottom: 22 }}>
          {[['login', 'Entrar'], ['register', 'Soy nuevo']].map(([m, txt]) => (
            <button key={m} onClick={() => { setModo(m); setError('') }}
              style={{
                flex: 1, padding: '12px', borderRadius: 999, border: 'none', fontWeight: 800,
                fontSize: 'clamp(15px,4vw,17px)', cursor: 'pointer',
                background: modo === m ? T.verde : 'transparent',
                color: modo === m ? '#fff' : T.suave,
                boxShadow: modo === m ? '0 4px 0 rgba(0,0,0,0.12)' : 'none',
              }}>
              {txt}
            </button>
          ))}
        </div>

        <form onSubmit={submit}>
          {modo === 'register' && (
            <>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontWeight: 700, fontSize: 14, color: T.suave, marginBottom: 6 }}>¿Quién eres?</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  {[['alumno', '👦 Soy alumno'], ['docente', '🧑‍🏫 Soy docente']].map(([r, txt]) => (
                    <button type="button" key={r} onClick={() => set('rol')(r)}
                      style={{
                        flex: 1, padding: '12px', borderRadius: 14, cursor: 'pointer', fontWeight: 800, fontSize: 14,
                        border: `2px solid ${form.rol === r ? T.verde : T.borde}`,
                        background: form.rol === r ? '#eafaf1' : '#fff',
                        color: form.rol === r ? T.verdeD : T.suave,
                      }}>
                      {txt}
                    </button>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <div style={{ flex: '1 1 140px' }}><Campo label="Nombre" value={form.nombre} onChange={set('nombre')} placeholder="Ana" /></div>
                <div style={{ flex: '1 1 140px' }}><Campo label="Apellido" value={form.apellido} onChange={set('apellido')} placeholder="Lopez" /></div>
              </div>
              {form.rol === 'alumno' && (
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  <div style={{ flex: '1 1 100px' }}><Campo label="Grado" value={form.grado} onChange={set('grado')} placeholder="1ro" /></div>
                  <div style={{ flex: '1 1 100px' }}><Campo label="Seccion" value={form.seccion} onChange={set('seccion')} placeholder="A" /></div>
                </div>
              )}
            </>
          )}
          <Campo label="Usuario" value={form.username} onChange={set('username')} placeholder="mi.usuario" />
          <Campo label="Contrasena" type="password" value={form.password} onChange={set('password')} placeholder="••••••" />

          {error && (
            <p style={{ background: '#fdecec', color: T.err, fontWeight: 700, fontSize: 14, margin: '0 0 14px', padding: '10px 14px', borderRadius: 14 }}>
              {error}
            </p>
          )}

          <Boton type="submit" disabled={cargando} color={T.verde}>
            {cargando ? 'Cargando…' : modo === 'login' ? '🎤  ¡Entrar!' : '🌟  Crear mi cuenta'}
          </Boton>
        </form>
      </Tarjeta>

      <p style={{ textAlign: 'center', color: T.suave, fontSize: 13, marginTop: 16 }}>SRV — Sistema de Retroalimentación por Voz</p>
    </Pantalla>
  )
}
