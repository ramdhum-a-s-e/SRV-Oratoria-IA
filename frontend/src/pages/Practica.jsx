import { useRef, useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import WaveSurfer from 'wavesurfer.js'
import RecordPlugin from 'wavesurfer.js/dist/plugins/record.js'
import api from '../api'

const C = {
  bg: '#0f172a', card: '#1e293b', border: '#334155', text: '#f1f5f9', muted: '#94a3b8',
  blue: '#6366f1', green: '#22c55e', greenBg: '#14532d', yellow: '#facc15', yellowBg: '#713f12',
  red: '#f87171', redBg: '#7f1d1d', purple: '#a78bfa', purpleBg: '#2e1065',
  orange: '#fb923c', orangeBg: '#7c2d12',
}
const THEME = {
  green:  { bg: C.greenBg,  border: C.green,  text: C.green },
  yellow: { bg: C.yellowBg, border: C.yellow, text: C.yellow },
  red:    { bg: C.redBg,    border: C.red,    text: C.red },
}

function hablar(texto) {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(texto)
  u.lang = 'es-PE'; u.rate = 0.9
  window.speechSynthesis.speak(u)
}

function Estrellas({ n, color }) {
  return (
    <div style={{ fontSize: '30px', letterSpacing: '4px', margin: '6px 0' }}>
      {[1,2,3,4,5].map(i => (
        <span key={i} style={{ opacity: i <= n ? 1 : 0.2, color: color || C.yellow }}>★</span>
      ))}
    </div>
  )
}

function BarraVelocidad({ ppm }) {
  const pct = Math.min(100, Math.max(0, ((ppm - 40) / 140) * 100))
  const zonaOkLeft  = ((80 - 40) / 140) * 100
  const zonaOkWidth = (40 / 140) * 100
  const color = ppm >= 80 && ppm <= 120 ? C.green : ppm > 120 ? C.red : C.yellow
  return (
    <div style={{ margin: '10px 0' }}>
      <div style={{ position: 'relative', height: '24px', borderRadius: '999px', backgroundColor: '#1e293b', border: `1px solid ${C.border}`, overflow: 'hidden' }}>
        <div style={{ position: 'absolute', left: `${zonaOkLeft}%`, width: `${zonaOkWidth}%`, height: '100%', backgroundColor: '#14532d', opacity: 0.6 }} />
        <div style={{ position: 'absolute', left: `${pct}%`, transform: 'translateX(-50%)', top: '2px', bottom: '2px', width: '6px', borderRadius: '999px', backgroundColor: color, boxShadow: `0 0 8px ${color}` }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: C.muted, marginTop: '3px' }}>
        <span>Muy lento</span><span style={{ color: C.green }}>Ideal: 80-120 PPM</span><span>Muy rapido</span>
      </div>
    </div>
  )
}

function ScoreBar({ score, color }) {
  return (
    <div style={{ margin: '6px 0 10px' }}>
      <div style={{ height: '8px', borderRadius: '999px', backgroundColor: C.border, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${score}%`, borderRadius: '999px', backgroundColor: color }} />
      </div>
      <p style={{ fontSize: '11px', color: C.muted, margin: '2px 0 0', textAlign: 'right' }}>{score} / 100 pts</p>
    </div>
  )
}

function Tarjeta({ titulo, accentColor, children }) {
  return (
    <div style={{ backgroundColor: C.card, border: `1px solid ${accentColor || C.border}`, borderRadius: '12px', padding: '16px 18px', marginBottom: '12px', textAlign: 'left' }}>
      <p style={{ margin: '0 0 10px', fontWeight: 'bold', color: accentColor || C.text, fontSize: '13px' }}>{titulo}</p>
      {children}
    </div>
  )
}

function Fila({ label, valor, color }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: `1px solid ${C.border}` }}>
      <span style={{ fontSize: '12px', color: C.muted }}>{label}</span>
      <span style={{ fontSize: '12px', fontWeight: 'bold', color: color || C.text }}>{valor}</span>
    </div>
  )
}

/* ── Score Global ─────────────────────────────────────────────────────────── */
function ScoreGlobal({ data }) {
  const sg = data.score_global
  const t = THEME[sg.color] || THEME.green
  const d = sg.scores_por_dimension
  return (
    <div style={{ backgroundColor: t.bg, border: `2px solid ${t.border}`, borderRadius: '16px', padding: '22px 20px', marginBottom: '14px', textAlign: 'center' }}>
      <p style={{ margin: '0 0 2px', fontSize: '11px', color: t.text, textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '1px' }}>Resultado Final</p>
      <p style={{ fontSize: '52px', fontWeight: 'bold', color: t.text, margin: '4px 0 0', lineHeight: 1 }}>{sg.score_global}</p>
      <p style={{ fontSize: '12px', color: t.text, margin: '2px 0 6px', opacity: 0.8 }}>puntos de 100</p>
      <Estrellas n={sg.estrellas} color={t.text} />
      <p style={{ fontSize: '18px', fontWeight: 'bold', color: t.text, margin: '6px 0 4px' }}>{sg.nivel}</p>
      <p style={{ fontSize: '14px', color: t.text, margin: 0 }}>{sg.mensaje}</p>
      <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
        {[['D1 Fluidez', d.d1, C.blue], ['D2 Vocabulario', d.d2, C.purple], ['D3 Expresividad', d.d3, C.orange]].map(([lbl, val, col]) => (
          <div key={lbl} style={{ backgroundColor: 'rgba(0,0,0,0.25)', borderRadius: '8px', padding: '10px 6px' }}>
            <p style={{ fontSize: '10px', color: t.text, margin: '0 0 4px', opacity: 0.8 }}>{lbl}</p>
            <p style={{ fontSize: '22px', fontWeight: 'bold', color: col, margin: '0 0 4px' }}>{val}</p>
            <div style={{ height: '4px', borderRadius: '2px', backgroundColor: 'rgba(255,255,255,0.1)' }}>
              <div style={{ height: '100%', width: `${val}%`, borderRadius: '2px', backgroundColor: col }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ── Desplegable de datos técnicos por dimensión ──────────────────────────── */
function DatosTecnicos({ rows, accentColor }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ marginTop: '12px' }}>
      <button onClick={() => setOpen(v => !v)}
        style={{ width: '100%', padding: '7px 12px', borderRadius: '8px', border: `1px solid ${C.border}`, backgroundColor: 'rgba(0,0,0,0.2)', color: C.muted, cursor: 'pointer', fontSize: '11px', textAlign: 'left' }}>
        {open ? '▲' : '▼'} Datos tecnicos (para el docente)
      </button>
      {open && (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', color: C.text, marginTop: '6px' }}>
          <tbody>
            {rows.map(([k, v]) => (
              <tr key={k} style={{ borderBottom: `1px solid ${C.border}` }}>
                <td style={{ padding: '4px 8px', color: C.muted }}>{k}</td>
                <td style={{ padding: '4px 8px', fontWeight: '500', textAlign: 'right', color: accentColor || C.text }}>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

/* ── D1 ───────────────────────────────────────────────────────────────────── */
function SeccionD1({ data }) {
  const fb = data.retroalimentacion
  const t  = THEME[fb.color] || THEME.green
  const ttsTexto = `${fb.mensaje_principal}. ${fb.detalle_velocidad}. ${fb.detalle_pausas}.`
  const tecnico = [
    ['PPM', `${data.ppm.ppm} PPM`],
    ['Palabras detectadas', data.ppm.word_count],
    ['Duracion habla', `${data.ppm.speech_duration_s}s`],
    ['Pausas cortas', data.pausas.total_pauses],
    ['Pausas largas (bloqueos)', data.pausas.long_pauses],
    ['Pausa promedio', data.pausas.avg_pause_s != null ? `${data.pausas.avg_pause_s}s` : 'N/A'],
  ]
  return (
    <Tarjeta titulo="D1 — Fluidez oral" accentColor={C.blue}>
      {/* Encabezado con estrellas */}
      <div style={{ backgroundColor: t.bg, border: `1px solid ${t.border}`, borderRadius: '10px', padding: '12px', marginBottom: '14px', textAlign: 'center' }}>
        <p style={{ fontSize: '16px', fontWeight: 'bold', color: t.text, margin: 0 }}>{fb.mensaje_principal}</p>
        <Estrellas n={fb.estrellas} color={t.text} />
        <button onClick={() => hablar(ttsTexto)}
          style={{ marginTop: '2px', padding: '5px 14px', borderRadius: '999px', border: `1px solid ${t.border}`, backgroundColor: 'transparent', color: t.text, cursor: 'pointer', fontSize: '12px' }}>
          🔊 Escuchar resultado
        </button>
      </div>

      {/* Velocidad de habla */}
      <p style={{ margin: '0 0 4px', fontSize: '12px', fontWeight: 'bold', color: C.text }}>Velocidad de habla</p>
      <BarraVelocidad ppm={data.ppm.ppm} />
      <Fila label="Palabras por minuto" valor={`${data.ppm.ppm} PPM`} color={data.ppm.ppm >= 80 && data.ppm.ppm <= 120 ? C.green : C.yellow} />
      <p style={{ margin: '8px 0 14px', color: C.muted, fontSize: '13px' }}>{fb.detalle_velocidad}</p>

      {/* Bloqueos */}
      <p style={{ margin: '0 0 6px', fontSize: '12px', fontWeight: 'bold', color: C.text }}>Bloqueos</p>
      <div style={{ display: 'flex', gap: '20px', margin: '4px 0 10px' }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '40px', fontWeight: 'bold', margin: 0, color: data.pausas.long_pauses === 0 ? C.green : C.red }}>{data.pausas.long_pauses}</p>
          <p style={{ fontSize: '11px', color: C.muted, margin: 0 }}>bloqueos</p>
        </div>
      </div>
      <p style={{ margin: '0 0 14px', color: C.muted, fontSize: '13px' }}>{fb.detalle_pausas}</p>

      {/* Volumen */}
      <p style={{ margin: '0 0 4px', fontSize: '12px', fontWeight: 'bold', color: C.text }}>Volumen</p>
      <Fila label="Volumen de voz" valor={data.prosodia?.intensity_mean_db != null ? `${data.prosodia.intensity_mean_db} dB` : 'N/A'} />
      {data.d3?.detalle_volumen && <p style={{ margin: '8px 0 0', color: C.muted, fontSize: '13px' }}>{data.d3.detalle_volumen}</p>}

      <DatosTecnicos rows={tecnico} accentColor={C.blue} />
    </Tarjeta>
  )
}

/* ── D2 ───────────────────────────────────────────────────────────────────── */
function SeccionD2({ d2 }) {
  const colMul = d2.muletillas_count === 0 ? C.green : d2.muletillas_count <= 3 ? C.yellow : C.red
  const colTTR = d2.ttr_score > 0.5 ? C.green : d2.ttr_score > 0.3 ? C.yellow : C.red
  // El color de coherencia usa el nivel cualitativo del backend (BETO da rango alto)
  const colCoh = d2.coherencia_nivel === 'bueno' ? C.green : d2.coherencia_nivel === 'regular' ? C.yellow : C.red
  const tecnico = [
    ['Palabras de contenido', d2.word_count_d2],
    ['Palabras unicas', d2.unique_words],
    ['TTR (riqueza lexica)', d2.ttr_score],
    ['Muletillas (total)', d2.muletillas_count],
    ['Tasa de muletillas', d2.muletillas_tasa != null ? `${d2.muletillas_tasa}%` : 'N/A'],
    ['Coherencia (BETO)', d2.coherencia_score],
    ['Metodo coherencia', d2.coherencia_metodo || 'N/A'],
  ]
  if (d2.por_tipo) {
    for (const [tipo, n] of Object.entries(d2.por_tipo)) tecnico.push([`  · "${tipo}"`, n])
  }
  return (
    <Tarjeta titulo="D2 — Vocabulario y coherencia" accentColor={C.purple}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
        {[
          ['Muletillas', d2.muletillas_count, '', colMul],
          ['Variedad',   `${Math.round(d2.ttr_score * 100)}%`, 'TTR', colTTR],
          ['Coherencia', d2.coherencia_nivel || '—', '', colCoh],
        ].map(([lbl, val, sub, col]) => (
          <div key={lbl} style={{ flex: 1, textAlign: 'center', backgroundColor: 'rgba(167,139,250,0.08)', borderRadius: '8px', padding: '10px 4px' }}>
            <p style={{ fontSize: '26px', fontWeight: 'bold', margin: 0, color: col }}>{val}</p>
            {sub && <p style={{ fontSize: '9px', color: C.muted, margin: 0 }}>{sub}</p>}
            <p style={{ fontSize: '11px', color: C.muted, margin: '2px 0 0' }}>{lbl}</p>
          </div>
        ))}
      </div>
      <ScoreBar score={d2.score_d2} color={C.purple} />
      <p style={{ margin: '4px 0', color: C.muted, fontSize: '12px' }}>{d2.detalle_muletillas}</p>
      <p style={{ margin: '4px 0', color: C.muted, fontSize: '12px' }}>{d2.detalle_vocabulario}</p>
      <p style={{ margin: '4px 0', color: C.muted, fontSize: '12px' }}>{d2.detalle_coherencia}</p>
      {d2.muletillas_list?.length > 0 && (
        <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
          {d2.muletillas_list.map(m => (
            <span key={m} style={{ padding: '2px 10px', borderRadius: '999px', backgroundColor: 'rgba(251,146,60,0.15)', border: `1px solid ${C.orange}`, color: C.orange, fontSize: '11px' }}>{m}</span>
          ))}
        </div>
      )}
      <DatosTecnicos rows={tecnico} accentColor={C.purple} />
    </Tarjeta>
  )
}

/* ── D3 ───────────────────────────────────────────────────────────────────── */
function SeccionD3({ d3, prosodia }) {
  const p = prosodia || {}
  const tecnico = [
    ['F0 promedio', p.f0_mean_hz ? `${p.f0_mean_hz} Hz` : 'N/A'],
    ['F0 std (variacion)', p.f0_std_hz ? `${p.f0_std_hz} Hz` : 'N/A'],
    ['Jitter', p.jitter_pct != null ? `${p.jitter_pct}%` : 'N/A'],
    ['Shimmer', p.shimmer_db != null ? `${p.shimmer_db} dB` : 'N/A'],
    ['HNR (calidad voz)', p.hnr_db != null ? `${p.hnr_db} dB` : 'N/A'],
    ['Intensidad (volumen)', p.intensity_mean_db != null ? `${p.intensity_mean_db} dB` : 'N/A'],
  ]
  return (
    <Tarjeta titulo="D3 — Expresividad vocal" accentColor={C.orange}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
        {[
          ['Variacion tono', d3.breakdown.variacion_tonal_pts, 40, C.orange],
          ['Calidad voz',    d3.breakdown.calidad_hnr_pts,     30, C.yellow],
        ].map(([lbl, val, max, col]) => (
          <div key={lbl} style={{ flex: 1, textAlign: 'center', backgroundColor: 'rgba(251,146,60,0.08)', borderRadius: '8px', padding: '10px 4px' }}>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: 0, color: col }}>{val}</p>
            <p style={{ fontSize: '9px', color: C.muted, margin: 0 }}>/{max} pts</p>
            <p style={{ fontSize: '11px', color: C.muted, margin: '2px 0 0' }}>{lbl}</p>
          </div>
        ))}
      </div>
      <ScoreBar score={d3.score_d3} color={C.orange} />
      <p style={{ margin: '4px 0', color: C.muted, fontSize: '12px' }}>{d3.detalle_tono}</p>
      <p style={{ margin: '4px 0', color: C.muted, fontSize: '12px' }}>{d3.detalle_calidad}</p>
      <DatosTecnicos rows={tecnico} accentColor={C.orange} />
    </Tarjeta>
  )
}

/* ── Resultados completos ─────────────────────────────────────────────────── */
function Resultados({ data }) {
  const todosConsejos = [...(data.retroalimentacion?.consejos || []), ...(data.d2?.consejos || [])]
  return (
    <div style={{ maxWidth: '680px', margin: '18px auto', textAlign: 'center' }}>
      <ScoreGlobal data={data} />
      {data.lectura && (
        <Tarjeta titulo="Modo lectura — Fidelidad" accentColor={data.lectura.fidelidad_score >= 70 ? C.green : data.lectura.fidelidad_score >= 50 ? C.yellow : C.red}>
          <div style={{ textAlign: 'center', margin: '4px 0 8px' }}>
            <p style={{ fontSize: '44px', fontWeight: 'bold', margin: 0, lineHeight: 1, color: data.lectura.fidelidad_score >= 70 ? C.green : data.lectura.fidelidad_score >= 50 ? C.yellow : C.red }}>{data.lectura.fidelidad_score}%</p>
            <p style={{ fontSize: '11px', color: C.muted, margin: '2px 0 0' }}>coincidencia con el texto</p>
          </div>
          <p style={{ margin: '4px 0 8px', color: C.muted, fontSize: '13px' }}>{data.lectura.mensaje}</p>
          <Fila label="Palabras del texto" valor={data.lectura.palabras_texto} />
          <Fila label="Palabras leidas"  valor={data.lectura.palabras_leidas} />
        </Tarjeta>
      )}
      <SeccionD1 data={data} />
      <SeccionD2 d2={data.d2} />
      <SeccionD3 d3={data.d3} prosodia={data.prosodia} />
      {todosConsejos.length > 0 && (
        <div style={{ backgroundColor: '#1e3a5f', border: '1px solid #2563eb', borderRadius: '12px', padding: '14px 18px', marginBottom: '12px', textAlign: 'left' }}>
          <p style={{ margin: '0 0 6px', fontWeight: 'bold', color: '#93c5fd', fontSize: '13px' }}>💡 Para mejorar:</p>
          {todosConsejos.map((c, i) => <p key={i} style={{ margin: '3px 0', color: '#bfdbfe', fontSize: '13px' }}>• {c}</p>)}
        </div>
      )}
      <Tarjeta titulo="Lo que dijiste">
        <p style={{ margin: 0, color: C.text, fontSize: '13px', lineHeight: '1.7', fontStyle: 'italic' }}>"{data.transcripcion || '(no se detecto texto)'}"</p>
      </Tarjeta>
    </div>
  )
}

/* ── Página principal ─────────────────────────────────────────────────────── */
export default function Practica() {
  const [params]  = useSearchParams()
  const navigate  = useNavigate()
  const modo      = params.get('modo') || 'libre'
  const textoId   = params.get('texto_id')

  const [texto,      setTexto]     = useState(null)
  const containerRef               = useRef(null)
  const wavesurferRef              = useRef(null)
  const recordRef                  = useRef(null)
  const [grabando,   setGrabando]  = useState(false)
  const [analizando, setAnalizando]= useState(false)
  const [resultado,  setResultado] = useState(null)
  const [error,      setError]     = useState(null)

  useEffect(() => {
    if (modo === 'lectura' && textoId) {
      api.get('/audio/textos').then(r => {
        const t = r.data.find(x => x.id === parseInt(textoId))
        if (t) setTexto(t)
      })
    }
  }, [modo, textoId])

  const manejarGrabacion = async () => {
    if (!grabando) {
      if (wavesurferRef.current) wavesurferRef.current.destroy()
      setResultado(null); setError(null)
      const ws = WaveSurfer.create({ container: containerRef.current, waveColor: C.blue, height: 80 })
      const record = ws.registerPlugin(RecordPlugin.create())
      try {
        await record.startRecording()
        wavesurferRef.current = ws; recordRef.current = record
        setGrabando(true)
        hablar('Puedes empezar a hablar')
      } catch { setError('No se pudo acceder al microfono.') }
    } else {
      setGrabando(false)
      recordRef.current.stopRecording()
      recordRef.current.on('record-end', async blob => {
        setAnalizando(true)
        const fd = new FormData()
        fd.append('file', blob, 'practica.wav')
        fd.append('modo', modo)
        if (textoId) fd.append('texto_id', textoId)
        try {
          const res = await api.post('/audio/analizar', fd)
          setResultado(res.data)
          hablar(res.data.score_global.mensaje)
        } catch (err) {
          if (err.response?.status === 401) { navigate('/login'); return }
          setError('Error al analizar. Verifica que el servidor este encendido.')
        } finally { setAnalizando(false) }
      })
    }
  }

  return (
    <div style={{ padding: '28px 20px', textAlign: 'center', backgroundColor: C.bg, color: C.text, minHeight: '100vh', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ maxWidth: '680px', margin: '0 auto' }}>
        <button onClick={() => navigate('/modos')}
          style={{ background: 'none', border: 'none', color: C.muted, cursor: 'pointer', fontSize: '13px', marginBottom: '14px', padding: 0, display: 'block' }}>
          ← Cambiar modo
        </button>
        <h1 style={{ fontSize: '20px', margin: '0 0 4px' }}>
          {modo === 'lectura' ? '📖 Practica de lectura' : '🎙️ Expresion oral libre'}
        </h1>
        <p style={{ color: C.muted, margin: '0 0 18px', fontSize: '13px' }}>
          {modo === 'lectura' ? 'Lee el texto en voz alta' : 'Habla sobre el tema que quieras'}
        </p>
        {texto && (
          <div style={{ backgroundColor: C.card, border: `1px solid ${C.border}`, borderRadius: '12px', padding: '18px', marginBottom: '18px', textAlign: 'left' }}>
            <p style={{ color: C.muted, fontSize: '11px', margin: '0 0 6px', textTransform: 'uppercase', fontWeight: 'bold' }}>{texto.titulo}</p>
            <p style={{ color: C.text, fontSize: '16px', lineHeight: '1.8', margin: 0 }}>{texto.contenido}</p>
          </div>
        )}
        {modo === 'libre' && !resultado && (
          <div style={{ backgroundColor: '#1e3a5f', border: '1px solid #2563eb', borderRadius: '10px', padding: '12px 16px', marginBottom: '18px' }}>
            <p style={{ color: '#93c5fd', margin: 0, fontSize: '13px' }}>💡 Habla sobre: tu dia, tu animal favorito, tu familia, una pelicula que viste...</p>
          </div>
        )}
        <div ref={containerRef} style={{ margin: '0 auto 18px', width: '100%', minHeight: '80px', border: `1px solid ${C.border}`, borderRadius: '12px', overflow: 'hidden', backgroundColor: C.card }} />
        <button onClick={manejarGrabacion} disabled={analizando}
          style={{ padding: '16px 44px', fontSize: '17px', fontWeight: 'bold', borderRadius: '999px', border: 'none',
            cursor: analizando ? 'not-allowed' : 'pointer',
            backgroundColor: analizando ? '#374151' : grabando ? '#dc2626' : C.blue,
            color: 'white', boxShadow: grabando ? '0 0 20px rgba(220,38,38,0.5)' : analizando ? 'none' : `0 0 20px rgba(99,102,241,0.4)` }}>
          {analizando ? 'Analizando...' : grabando ? '⏹  Listo, analizar' : '🎤  Empezar a hablar'}
        </button>
        {grabando   && <p style={{ color: C.red,  marginTop: '10px', fontSize: '14px' }}>Grabando... cuando termines presiona el boton</p>}
        {analizando && <p style={{ color: C.muted, marginTop: '14px', fontSize: '13px' }}>Procesando tu voz con IA, espera un momento...</p>}
        {error      && <div style={{ marginTop: '14px', backgroundColor: C.redBg, border: `1px solid ${C.red}`, borderRadius: '10px', padding: '12px', color: C.red, fontSize: '13px' }}>{error}</div>}
        {resultado  && <Resultados data={resultado} />}
        {resultado  && (
          <button onClick={() => navigate('/historial')}
            style={{ marginTop: '14px', padding: '10px 24px', borderRadius: '8px', border: `1px solid ${C.border}`, backgroundColor: 'transparent', color: C.muted, cursor: 'pointer', fontSize: '13px' }}>
            Ver mi historial →
          </button>
        )}
      </div>
    </div>
  )
}
