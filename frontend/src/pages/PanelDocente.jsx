import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { T, colorScore } from '../ui/theme'
import { Lorito } from '../ui/kit'

const BB = "'Baloo 2', sans-serif"

function PillBtn({ children, onClick }) {
  return (
    <button onClick={onClick}
      style={{ padding: '9px 16px', borderRadius: 999, border: `2px solid ${T.borde}`, background: '#fff', color: T.suave, cursor: 'pointer', fontWeight: 700, fontSize: 13 }}>
      {children}
    </button>
  )
}

/* ── Detalle de un alumno ──────────────────────────────────────────────────── */
function DetalleAlumno({ alumnoId, onVolver }) {
  const [data, setData] = useState(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    api.get(`/metrics/docente/alumno/${alumnoId}`)
      .then(r => setData(r.data))
      .finally(() => setCargando(false))
  }, [alumnoId])

  const descargarPDF = async (id) => {
    try {
      const res = await api.get(`/metrics/reporte/${id}`, { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url; a.download = `reporte_sesion_${id}.pdf`
      document.body.appendChild(a); a.click(); a.remove()
      URL.revokeObjectURL(url)
    } catch { /* noop */ }
  }

  if (cargando) return <p style={{ color: T.suave, textAlign: 'center' }}>Cargando…</p>
  if (!data) return null
  const a = data.alumno

  return (
    <div className="aparecer">
      <PillBtn onClick={onVolver}>← Volver a la lista</PillBtn>
      <h2 style={{ margin: '14px 0 2px' }}>{a.nombre} {a.apellido}</h2>
      <p style={{ color: T.suave, margin: '0 0 16px', fontWeight: 700 }}>{a.grado || ''} {a.seccion || ''} · {data.sesiones.length} prácticas</p>

      {data.sesiones.length === 0 && (
        <p style={{ color: T.suave }}>Este alumno aún no tiene prácticas.</p>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {data.sesiones.map(s => (
          <div key={s.id} style={{ background: '#fff', border: `2px solid ${T.borde}`, borderRadius: 16, padding: '14px 16px', boxShadow: T.sombra }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
              <div>
                <p style={{ margin: 0, color: T.texto, fontWeight: 800, fontSize: 14 }}>
                  {s.modo === 'lectura' ? '📖 Lectura' : '🎤 Expresion libre'}
                </p>
                <p style={{ margin: '2px 0 8px', color: T.suave, fontSize: 11 }}>
                  {new Date(s.created_at).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </p>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {[['Fluidez', s.score_d1, T.d1], ['Vocab.', s.score_d2, T.d2], ['Expres.', s.score_d3, T.d3]].map(([lbl, val, col]) =>
                    val != null ? (
                      <span key={lbl} style={{ fontSize: 11, padding: '3px 9px', borderRadius: 999, background: col + '18', color: col, fontWeight: 700 }}>
                        {lbl}: {val}
                      </span>
                    ) : null
                  )}
                </div>
                <button onClick={() => descargarPDF(s.id)}
                  style={{ marginTop: 10, padding: '6px 12px', borderRadius: 999, border: `2px solid ${T.coral}`, background: '#fff', color: T.coral, cursor: 'pointer', fontSize: 11, fontWeight: 700 }}>
                  📄 PDF
                </button>
              </div>
              <div style={{ textAlign: 'right' }}>
                {s.score_global != null && (
                  <>
                    <p style={{ fontSize: 26, fontWeight: 800, margin: '0 0 2px', color: colorScore(s.score_global), fontFamily: BB }}>{s.score_global}</p>
                    <p style={{ fontSize: 9, color: T.suave, margin: 0 }}>pts global</p>
                  </>
                )}
                <p style={{ margin: '4px 0 0', color: T.suave, fontSize: 11 }}>{s.ppm ? `${s.ppm} PPM` : ''}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ── Panel principal ───────────────────────────────────────────────────────── */
export default function PanelDocente() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [alumnos, setAlumnos] = useState([])
  const [cargando, setCargando] = useState(true)
  const [sel, setSel] = useState(null)

  useEffect(() => {
    api.get('/metrics/docente/alumnos')
      .then(r => setAlumnos(r.data))
      .catch(err => { if (err.response?.status === 401) navigate('/login') })
      .finally(() => setCargando(false))
  }, [])

  return (
    <div style={{ minHeight: '100svh', padding: '24px 18px 40px' }}>
      <div style={{ maxWidth: 760, margin: '0 auto' }}>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18, gap: 10, flexWrap: 'wrap' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 'clamp(22px,5.5vw,30px)' }}>🧑‍🏫 Panel del docente</h1>
            <p style={{ color: T.suave, margin: 0, fontWeight: 700 }}>{user?.nombre} {user?.apellido}</p>
          </div>
          <PillBtn onClick={logout}>Salir</PillBtn>
        </div>

        {sel ? (
          <DetalleAlumno alumnoId={sel} onVolver={() => setSel(null)} />
        ) : (
          <>
            {cargando && <p style={{ color: T.suave, textAlign: 'center' }}>Cargando…</p>}
            {!cargando && alumnos.length === 0 && (
              <div style={{ textAlign: 'center', padding: '10px 0' }}>
                <Lorito size={84} mensaje="Aún no hay alumnos registrados" />
              </div>
            )}
            {!cargando && alumnos.length > 0 && (
              <>
                <p style={{ color: T.suave, fontWeight: 700, marginBottom: 12 }}>{alumnos.length} alumno(s) · toca uno para ver su detalle</p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
                  {alumnos.map(a => (
                    <button key={a.id} onClick={() => setSel(a.id)}
                      style={{ textAlign: 'left', background: '#fff', border: `2px solid ${T.borde}`, borderRadius: 18, padding: 16, cursor: 'pointer', boxShadow: T.sombra }}>
                      <p style={{ margin: '0 0 2px', color: T.texto, fontWeight: 800, fontSize: 16 }}>{a.nombre} {a.apellido}</p>
                      <p style={{ margin: '0 0 10px', color: T.suave, fontSize: 12, fontWeight: 700 }}>{a.grado || ''} {a.seccion || ''}</p>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <p style={{ margin: 0, fontSize: 11, color: T.suave }}>Promedio</p>
                          <p style={{ margin: 0, fontSize: 24, fontWeight: 800, color: colorScore(a.promedio), fontFamily: BB }}>{a.promedio ?? '—'}</p>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <p style={{ margin: 0, fontSize: 11, color: T.suave }}>Prácticas</p>
                          <p style={{ margin: 0, fontSize: 24, fontWeight: 800, color: T.cielo, fontFamily: BB }}>{a.practicas}</p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
