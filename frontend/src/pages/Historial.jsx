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

/* ── HU-26: gráfico de línea con tendencia (regresión lineal) ──────────────── */
function GraficoLinea({ titulo, datos, color }) {
  const puntos = datos.filter(d => d.v != null)
  const cardStyle = { backgroundColor: C.card, border: `1px solid ${C.border}`, borderRadius: '12px', padding: '12px 16px', marginBottom: '10px' }
  const tituloStyle = { color: C.text, fontSize: '12px', margin: 0, fontWeight: 'bold' }

  if (puntos.length < 2) {
    return (
      <div style={cardStyle}>
        <p style={tituloStyle}>{titulo}</p>
        <p style={{ color: C.muted, fontSize: '11px', margin: '4px 0 0' }}>Necesitas al menos 2 practicas para ver tu progreso.</p>
      </div>
    )
  }

  const W = 300, H = 90, P = 8
  const n  = puntos.length
  const xs = puntos.map((_, i) => P + (i / (n - 1)) * (W - 2 * P))
  const ty = v => H - P - (Math.max(0, Math.min(100, v)) / 100) * (H - 2 * P)
  const ys = puntos.map(p => ty(p.v))
  const path = xs.map((x, i) => `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${ys[i].toFixed(1)}`).join(' ')

  // Regresión lineal simple (mínimos cuadrados) sobre el índice de la práctica
  const meanX = (n - 1) / 2
  const meanY = puntos.reduce((a, p) => a + p.v, 0) / n
  let num = 0, den = 0
  puntos.forEach((p, i) => { num += (i - meanX) * (p.v - meanY); den += (i - meanX) ** 2 })
  const slope  = den ? num / den : 0
  const yStart = meanY + slope * (0 - meanX)
  const yEnd   = meanY + slope * ((n - 1) - meanX)
  const delta  = slope * (n - 1)  // cambio total estimado en el rango
  const tend = delta > 3  ? { txt: '↑ Vas mejorando',       col: C.green }
             : delta < -3 ? { txt: '↓ Estas bajando',        col: C.red }
             :              { txt: '→ Te mantienes estable',  col: C.yellow }

  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
        <p style={tituloStyle}>{titulo}</p>
        <span style={{ fontSize: '11px', fontWeight: 'bold', color: tend.col }}>{tend.txt}</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ display: 'block' }}>
        {[50, 70].map(g => (
          <line key={g} x1={P} y1={ty(g)} x2={W - P} y2={ty(g)} stroke={C.border} strokeWidth="1" strokeDasharray="3 3" />
        ))}
        <line x1={P} y1={ty(yStart)} x2={W - P} y2={ty(yEnd)} stroke={tend.col} strokeWidth="1.5" strokeDasharray="5 4" opacity="0.7" />
        <path d={path} fill="none" stroke={color} strokeWidth="2" />
        {xs.map((x, i) => <circle key={i} cx={x} cy={ys[i]} r="2.5" fill={color} />)}
      </svg>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: C.muted, marginTop: '2px' }}>
        <span>{puntos[0].t.toLocaleDateString('es-PE', { day: '2-digit', month: 'short' })}</span>
        <span>{puntos[n - 1].t.toLocaleDateString('es-PE', { day: '2-digit', month: 'short' })}</span>
      </div>
    </div>
  )
}

function ProgresoTemporal({ sesiones }) {
  const [rango, setRango] = useState('todo')
  const ahora  = Date.now()
  const limite = rango === 'semana' ? 7 : rango === 'mes' ? 30 : null
  const filtradas = sesiones
    .filter(s => limite == null || (ahora - new Date(s.created_at).getTime()) <= limite * 86400000)
    .slice().reverse()  // cronologico: de la mas antigua a la mas reciente

  const serie = key => filtradas.map(s => ({ t: new Date(s.created_at), v: s[key] }))

  return (
    <div style={{ marginBottom: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <p style={{ color: C.muted, fontSize: '11px', margin: 0, fontWeight: 'bold', textTransform: 'uppercase' }}>Progreso en el tiempo</p>
        <div style={{ display: 'flex', gap: '4px' }}>
          {[['semana', 'Semana'], ['mes', 'Mes'], ['todo', 'Todo']].map(([k, l]) => (
            <button key={k} onClick={() => setRango(k)}
              style={{ padding: '4px 10px', borderRadius: '6px', border: `1px solid ${rango === k ? C.blue : C.border}`, backgroundColor: rango === k ? 'rgba(99,102,241,0.15)' : 'transparent', color: rango === k ? C.blue : C.muted, cursor: 'pointer', fontSize: '11px' }}>
              {l}
            </button>
          ))}
        </div>
      </div>
      <GraficoLinea titulo="Score global"      datos={serie('score_global')} color={C.green} />
      <GraficoLinea titulo="D1 — Fluidez"      datos={serie('score_d1')}     color={C.blue} />
      <GraficoLinea titulo="D2 — Vocabulario"  datos={serie('score_d2')}     color={C.purple} />
      <GraficoLinea titulo="D3 — Expresividad" datos={serie('score_d3')}     color={C.orange} />
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

        <ProgresoTemporal sesiones={sesiones} />
        <MiniBarrasPPM    sesiones={sesiones} />

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
