import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../context/AuthContext'

const C = {
  bg: '#0f172a', card: '#1e293b', border: '#334155', text: '#f1f5f9', muted: '#94a3b8',
  blue: '#6366f1', green: '#22c55e', yellow: '#facc15', red: '#f87171',
  purple: '#a78bfa', orange: '#fb923c',
}

function colorStar(n) {
  if (n >= 4) return C.green
  if (n >= 3) return C.yellow
  return C.red
}
function colorScore(s) {
  if (s == null) return C.muted
  if (s >= 70) return C.green
  if (s >= 50) return C.yellow
  return C.red
}

function MiniBarrasPPM({ sesiones }) {
  if (!sesiones.length) return null
  const max = Math.max(...sesiones.map(s => s.ppm || 0), 130)
  return (
    <div style={{ backgroundColor: C.card, border: `1px solid ${C.border}`, borderRadius: '12px', padding: '14px 18px', marginBottom: '14px' }}>
      <p style={{ color: C.muted, fontSize: '11px', margin: '0 0 10px', fontWeight: 'bold', textTransform: 'uppercase' }}>Evolucion de PPM</p>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: '6px', height: '70px' }}>
        {sesiones.slice().reverse().map((s, i) => {
          const ppm = s.ppm || 0
          const h   = Math.max(4, (ppm / max) * 70)
          const ok  = ppm >= 80 && ppm <= 120
          return (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
              <span style={{ fontSize: '9px', color: C.muted }}>{ppm}</span>
              <div style={{ width: '100%', height: `${h}px`, borderRadius: '3px 3px 0 0', backgroundColor: ok ? C.green : ppm > 120 ? C.red : C.yellow, opacity: 0.8 }} />
            </div>
          )
        })}
      </div>
    </div>
  )
}

function MiniBarrasScore({ sesiones }) {
  const con = sesiones.filter(s => s.score_global != null)
  if (!con.length) return null
  return (
    <div style={{ backgroundColor: C.card, border: `1px solid ${C.border}`, borderRadius: '12px', padding: '14px 18px', marginBottom: '14px' }}>
      <p style={{ color: C.muted, fontSize: '11px', margin: '0 0 10px', fontWeight: 'bold', textTransform: 'uppercase' }}>Evolucion de Score Global</p>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: '6px', height: '70px' }}>
        {con.slice().reverse().map((s, i) => {
          const sc = s.score_global || 0
          const h  = Math.max(4, (sc / 100) * 70)
          return (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
              <span style={{ fontSize: '9px', color: C.muted }}>{sc}</span>
              <div style={{ width: '100%', height: `${h}px`, borderRadius: '3px 3px 0 0', backgroundColor: colorScore(sc), opacity: 0.8 }} />
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function Historial() {
  const { user }   = useAuth()
  const navigate   = useNavigate()
  const [sesiones, setSesiones] = useState([])
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    api.get('/metrics/historial')
      .then(r => setSesiones(r.data))
      .catch(err => { if (err.response?.status === 401) navigate('/login') })
      .finally(() => setCargando(false))
  }, [])

  const conScore     = sesiones.filter(s => s.score_global != null)
  const promEstrellas = sesiones.length
    ? (sesiones.reduce((a, s) => a + (s.estrellas || 0), 0) / sesiones.length).toFixed(1) : '-'
  const promGlobal   = conScore.length
    ? Math.round(conScore.reduce((a, s) => a + s.score_global, 0) / conScore.length) : '-'
  const promBloqueos = sesiones.length
    ? (sesiones.reduce((a, s) => a + (s.long_pauses || 0), 0) / sesiones.length).toFixed(1) : '-'

  return (
    <div style={{ minHeight: '100vh', backgroundColor: C.bg, fontFamily: 'system-ui, sans-serif', padding: '28px 18px' }}>
      <div style={{ maxWidth: '700px', margin: '0 auto' }}>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '22px' }}>
          <div>
            <h1 style={{ color: C.text, margin: 0, fontSize: '20px' }}>Mi historial</h1>
            <p style={{ color: C.muted, margin: 0, fontSize: '13px' }}>{user?.nombre} {user?.apellido}</p>
          </div>
          <button onClick={() => navigate('/modos')}
            style={{ padding: '7px 14px', borderRadius: '8px', border: `1px solid ${C.border}`, backgroundColor: 'transparent', color: C.muted, cursor: 'pointer', fontSize: '12px' }}>
            ← Volver
          </button>
        </div>

        {/* Tarjetas de resumen */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '10px', marginBottom: '16px' }}>
          {[
            { label: 'Practicas',       valor: sesiones.length,  color: C.blue },
            { label: 'Score promedio',  valor: promGlobal,       color: colorScore(typeof promGlobal === 'number' ? promGlobal : null) },
            { label: 'Prom. estrellas', valor: promEstrellas,    color: C.yellow },
            { label: 'Bloqueos prom.',  valor: promBloqueos,     color: parseFloat(promBloqueos) === 0 ? C.green : C.red },
          ].map(({ label, valor, color }) => (
            <div key={label} style={{ backgroundColor: C.card, border: `1px solid ${C.border}`, borderRadius: '10px', padding: '12px', textAlign: 'center' }}>
              <p style={{ fontSize: '24px', fontWeight: 'bold', color: color, margin: 0 }}>{valor}</p>
              <p style={{ fontSize: '10px', color: C.muted, margin: 0 }}>{label}</p>
            </div>
          ))}
        </div>

        <MiniBarrasScore sesiones={sesiones} />
        <MiniBarrasPPM   sesiones={sesiones} />

        {cargando && <p style={{ color: C.muted, textAlign: 'center' }}>Cargando...</p>}
        {!cargando && sesiones.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <p style={{ color: C.muted, fontSize: '15px' }}>Aun no tienes practicas registradas</p>
            <button onClick={() => navigate('/modos')}
              style={{ marginTop: '12px', padding: '12px 24px', borderRadius: '8px', border: 'none', backgroundColor: C.blue, color: 'white', cursor: 'pointer', fontWeight: 'bold' }}>
              Hacer mi primera practica
            </button>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {sesiones.map(s => (
            <div key={s.id} style={{ backgroundColor: C.card, border: `1px solid ${C.border}`, borderRadius: '10px', padding: '12px 16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <p style={{ margin: 0, color: C.text, fontWeight: 'bold', fontSize: '13px' }}>
                    {s.modo === 'lectura' ? '📖 Lectura' : '🎙️ Expresion libre'}
                  </p>
                  <p style={{ margin: '2px 0 6px', color: C.muted, fontSize: '11px' }}>
                    {new Date(s.created_at).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </p>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {[['D1', s.score_d1, C.blue], ['D2', s.score_d2, C.purple], ['D3', s.score_d3, C.orange]].map(([lbl, val, col]) =>
                      val != null ? (
                        <span key={lbl} style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '4px', backgroundColor: 'rgba(255,255,255,0.06)', color: col, fontWeight: 'bold' }}>
                          {lbl}: {val}
                        </span>
                      ) : null
                    )}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  {s.score_global != null && (
                    <>
                      <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '0 0 2px', color: colorScore(s.score_global) }}>{s.score_global}</p>
                      <p style={{ fontSize: '9px', color: C.muted, margin: '0 0 4px' }}>pts global</p>
                    </>
                  )}
                  <div style={{ fontSize: '16px', color: colorStar(s.estrellas) }}>
                    {'★'.repeat(s.estrellas || 0)}{'☆'.repeat(5 - (s.estrellas || 0))}
                  </div>
                  <p style={{ margin: '2px 0 0', color: C.muted, fontSize: '11px' }}>{s.ppm ? `${s.ppm} PPM` : ''}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
