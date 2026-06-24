import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, BarElement, Tooltip,
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { T, colorScore } from '../ui/theme'
import { Lorito } from '../ui/kit'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip)

const BB = "'Baloo 2', sans-serif"

function colorStar(n) {
  if (n >= 4) return T.verde
  if (n >= 3) return T.amarillo
  return T.coral
}

/* ── Barras de PPM con Chart.js ────────────────────────────────────────────── */
function MiniBarrasPPM({ sesiones }) {
  if (!sesiones.length) return null
  const datos = sesiones.slice().reverse()
  const ppms  = datos.map(s => s.ppm || 0)
  const colores = ppms.map(p => (p >= 80 && p <= 120 ? T.verde : p > 120 ? T.coral : T.amarillo))

  const data = {
    labels: datos.map((_, i) => i + 1),
    datasets: [{ data: ppms, backgroundColor: colores, borderRadius: 5, maxBarThickness: 26 }],
  }
  const options = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: ctx => `${ctx.parsed.y} PPM` } },
    },
    scales: {
      y: { beginAtZero: true, ticks: { font: { size: 9 }, color: T.suave }, grid: { color: '#f0e9da' } },
      x: { ticks: { font: { size: 9 }, color: T.suave }, grid: { display: false } },
    },
  }
  return (
    <div style={{ background: '#fff', border: `2px solid ${T.borde}`, borderRadius: 18, padding: '16px 18px', marginBottom: 14, boxShadow: T.sombra }}>
      <p style={{ color: T.suave, fontSize: 11, margin: '0 0 10px', fontWeight: 800, textTransform: 'uppercase' }}>Evolucion de PPM</p>
      <div style={{ height: 90 }}><Bar data={data} options={options} /></div>
    </div>
  )
}

/* ── HU-26: gráfico de línea (Chart.js) con tendencia (regresión lineal) ────── */
function GraficoLinea({ titulo, datos, color }) {
  const puntos = datos.filter(d => d.v != null)
  const cardStyle = { background: '#fff', border: `2px solid ${T.borde}`, borderRadius: 16, padding: '12px 16px', marginBottom: 10, boxShadow: T.sombra }
  const tituloStyle = { color: T.texto, fontSize: 13, margin: 0, fontWeight: 800, fontFamily: BB }

  if (puntos.length < 2) {
    return (
      <div style={cardStyle}>
        <p style={tituloStyle}>{titulo}</p>
        <p style={{ color: T.suave, fontSize: 12, margin: '4px 0 0' }}>Necesitas al menos 2 practicas para ver tu progreso.</p>
      </div>
    )
  }

  const n = puntos.length
  // Regresión lineal simple (mínimos cuadrados) sobre el índice de la práctica
  const meanX = (n - 1) / 2
  const meanY = puntos.reduce((a, p) => a + p.v, 0) / n
  let num = 0, den = 0
  puntos.forEach((p, i) => { num += (i - meanX) * (p.v - meanY); den += (i - meanX) ** 2 })
  const slope = den ? num / den : 0
  const trend = puntos.map((_, i) => Math.max(0, Math.min(100, meanY + slope * (i - meanX))))
  const delta = slope * (n - 1)  // cambio total estimado en el rango
  const tend = delta > 3  ? { txt: '↑ Vas mejorando',       col: T.verde }
             : delta < -3 ? { txt: '↓ Estas bajando',        col: T.coral }
             :              { txt: '→ Te mantienes estable',  col: T.amarillo }

  const labels = puntos.map(p => p.t.toLocaleDateString('es-PE', { day: '2-digit', month: 'short' }))
  const linea = (vals, col, dash, width, pts) => ({
    data: vals, borderColor: col, backgroundColor: col, borderDash: dash,
    borderWidth: width, pointRadius: pts, pointBackgroundColor: col, tension: 0.35, fill: false,
  })
  const data = {
    labels,
    datasets: [
      linea(puntos.map(p => p.v), color, [], 2.5, 3),       // serie real
      linea(trend, tend.col, [5, 4], 1.5, 0),               // tendencia
      linea(labels.map(() => 70), T.borde, [3, 3], 1, 0),   // meta alta
      linea(labels.map(() => 50), T.borde, [3, 3], 1, 0),   // meta media
    ],
  }
  const options = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { filter: ctx => ctx.datasetIndex === 0, callbacks: { label: ctx => `${ctx.parsed.y} pts` } },
    },
    scales: {
      y: { min: 0, max: 100, ticks: { stepSize: 25, font: { size: 9 }, color: T.suave }, grid: { color: '#f0e9da' } },
      x: { ticks: { font: { size: 9 }, color: T.suave, autoSkip: true, maxTicksLimit: 4 }, grid: { display: false } },
    },
  }
  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <p style={tituloStyle}>{titulo}</p>
        <span style={{ fontSize: 12, fontWeight: 800, color: tend.col }}>{tend.txt}</span>
      </div>
      <div style={{ height: 120 }}><Line data={data} options={options} /></div>
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
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, flexWrap: 'wrap', gap: 8 }}>
        <p style={{ color: T.suave, fontSize: 11, margin: 0, fontWeight: 800, textTransform: 'uppercase' }}>Progreso en el tiempo</p>
        <div style={{ display: 'flex', gap: 4 }}>
          {[['semana', 'Semana'], ['mes', 'Mes'], ['todo', 'Todo']].map(([k, l]) => (
            <button key={k} onClick={() => setRango(k)}
              style={{ padding: '6px 12px', borderRadius: 999, border: `2px solid ${rango === k ? T.cielo : T.borde}`, background: rango === k ? '#eaf5ff' : '#fff', color: rango === k ? T.cielo : T.suave, cursor: 'pointer', fontSize: 12, fontWeight: 700 }}>
              {l}
            </button>
          ))}
        </div>
      </div>
      <GraficoLinea titulo="Score global"      datos={serie('score_global')} color={T.verde} />
      <GraficoLinea titulo="Fluidez"           datos={serie('score_d1')}     color={T.d1} />
      <GraficoLinea titulo="Vocabulario"       datos={serie('score_d2')}     color={T.d2} />
      <GraficoLinea titulo="Expresividad"      datos={serie('score_d3')}     color={T.d3} />
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

  const conScore     = sesiones.filter(s => s.score_global != null)
  const promEstrellas = sesiones.length
    ? (sesiones.reduce((a, s) => a + (s.estrellas || 0), 0) / sesiones.length).toFixed(1) : '-'
  const promGlobal   = conScore.length
    ? Math.round(conScore.reduce((a, s) => a + s.score_global, 0) / conScore.length) : '-'
  const promBloqueos = sesiones.length
    ? (sesiones.reduce((a, s) => a + (s.long_pauses || 0), 0) / sesiones.length).toFixed(1) : '-'

  return (
    <div style={{ minHeight: '100svh', padding: '24px 18px 40px' }}>
      <div style={{ maxWidth: 700, margin: '0 auto' }}>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 22, gap: 10, flexWrap: 'wrap' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 'clamp(22px,5.5vw,28px)' }}>📊 Mi historial</h1>
            <p style={{ color: T.suave, margin: 0, fontWeight: 700 }}>{user?.nombre} {user?.apellido}</p>
          </div>
          <button onClick={() => navigate('/modos')}
            style={{ padding: '9px 16px', borderRadius: 999, border: `2px solid ${T.borde}`, background: '#fff', color: T.suave, cursor: 'pointer', fontSize: 13, fontWeight: 700 }}>
            ← Volver
          </button>
        </div>

        {/* Tarjetas de resumen */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: 10, marginBottom: 16 }}>
          {[
            { label: 'Practicas',       valor: sesiones.length,  color: T.cielo },
            { label: 'Score promedio',  valor: promGlobal,       color: colorScore(typeof promGlobal === 'number' ? promGlobal : null) },
            { label: 'Prom. estrellas', valor: promEstrellas,    color: T.amarillo },
            { label: 'Bloqueos prom.',  valor: promBloqueos,     color: parseFloat(promBloqueos) === 0 ? T.verde : T.coral },
          ].map(({ label, valor, color }) => (
            <div key={label} style={{ background: '#fff', border: `2px solid ${T.borde}`, borderRadius: 16, padding: 14, textAlign: 'center', boxShadow: T.sombra }}>
              <p style={{ fontSize: 26, fontWeight: 800, color, margin: 0, fontFamily: BB }}>{valor}</p>
              <p style={{ fontSize: 11, color: T.suave, margin: 0, fontWeight: 600 }}>{label}</p>
            </div>
          ))}
        </div>

        {!cargando && sesiones.length > 0 && (
          <>
            <ProgresoTemporal sesiones={sesiones} />
            <MiniBarrasPPM    sesiones={sesiones} />
          </>
        )}

        {cargando && <p style={{ color: T.suave, textAlign: 'center' }}>Cargando…</p>}
        {!cargando && sesiones.length === 0 && (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <Lorito size={84} mensaje="¡Aún no tienes prácticas!" />
            <button onClick={() => navigate('/modos')}
              style={{ marginTop: 16, padding: '14px 28px', borderRadius: 999, border: 'none', background: T.verde, color: '#fff', cursor: 'pointer', fontWeight: 800, fontSize: 16, fontFamily: BB, boxShadow: '0 5px 0 rgba(0,0,0,0.15)' }}>
              🎤 Hacer mi primera práctica
            </button>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {sesiones.map(s => (
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
                      <p style={{ fontSize: 9, color: T.suave, margin: '0 0 4px' }}>pts global</p>
                    </>
                  )}
                  <div style={{ fontSize: 16, color: colorStar(s.estrellas), letterSpacing: 1 }}>
                    {'★'.repeat(s.estrellas || 0)}<span style={{ color: '#e8e0cf' }}>{'★'.repeat(5 - (s.estrellas || 0))}</span>
                  </div>
                  <p style={{ margin: '2px 0 0', color: T.suave, fontSize: 11 }}>{s.ppm ? `${s.ppm} PPM` : ''}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
