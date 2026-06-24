import { useRef, useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import WaveSurfer from 'wavesurfer.js'
import RecordPlugin from 'wavesurfer.js/dist/plugins/record.js'
import api from '../api'
import { T } from '../ui/theme'
import { Lorito } from '../ui/kit'

/* Paleta de estado clara (verde/amarillo/rojo que devuelve el backend) */
const THEME = {
  green:  { bg: '#e8f7ef', border: T.verde,   text: T.verdeD },
  yellow: { bg: '#fff5d6', border: T.amarillo, text: '#9a7400' },
  red:    { bg: '#fdecec', border: T.coral,   text: T.err },
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
    <div style={{ fontSize: '32px', letterSpacing: '4px', margin: '6px 0', lineHeight: 1 }}>
      {[1, 2, 3, 4, 5].map(i => (
        <span key={i} style={{ color: i <= n ? (color || T.amarillo) : '#e8e0cf' }}>★</span>
      ))}
    </div>
  )
}

function BarraVelocidad({ ppm }) {
  const pct = Math.min(100, Math.max(0, ((ppm - 40) / 140) * 100))
  const zonaOkLeft  = ((80 - 40) / 140) * 100
  const zonaOkWidth = (40 / 140) * 100
  const color = ppm >= 80 && ppm <= 120 ? T.verde : ppm > 120 ? T.coral : T.amarillo
  return (
    <div style={{ margin: '10px 0' }}>
      <div style={{ position: 'relative', height: '24px', borderRadius: '999px', backgroundColor: '#f4eede', border: `1px solid ${T.borde}`, overflow: 'hidden' }}>
        <div style={{ position: 'absolute', left: `${zonaOkLeft}%`, width: `${zonaOkWidth}%`, height: '100%', backgroundColor: '#d9f7e6' }} />
        <div style={{ position: 'absolute', left: `${pct}%`, transform: 'translateX(-50%)', top: '2px', bottom: '2px', width: '6px', borderRadius: '999px', backgroundColor: color, boxShadow: `0 0 8px ${color}` }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: T.suave, marginTop: '3px' }}>
        <span>Muy lento</span><span style={{ color: T.verde, fontWeight: 700 }}>Ideal: 80-120 PPM</span><span>Muy rapido</span>
      </div>
    </div>
  )
}

function ScoreBar({ score, color }) {
  return (
    <div style={{ margin: '6px 0 10px' }}>
      <div style={{ height: '10px', borderRadius: '999px', backgroundColor: '#f4eede', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${score}%`, borderRadius: '999px', backgroundColor: color }} />
      </div>
      <p style={{ fontSize: '11px', color: T.suave, margin: '2px 0 0', textAlign: 'right' }}>{score} / 100 pts</p>
    </div>
  )
}

function Tarjeta({ titulo, accentColor, children }) {
  return (
    <div style={{ background: '#fff', border: `2px solid ${accentColor ? accentColor + '40' : T.borde}`, borderRadius: 20, padding: '18px 20px', marginBottom: 14, textAlign: 'left', boxShadow: T.sombra }}>
      {titulo && <p style={{ margin: '0 0 12px', fontWeight: 800, color: accentColor || T.texto, fontSize: 15, fontFamily: "'Baloo 2', sans-serif" }}>{titulo}</p>}
      {children}
    </div>
  )
}

function Fila({ label, valor, color }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: `1px solid ${T.borde}` }}>
      <span style={{ fontSize: '13px', color: T.suave }}>{label}</span>
      <span style={{ fontSize: '13px', fontWeight: 800, color: color || T.texto }}>{valor}</span>
    </div>
  )
}

/* ── Score Global ─────────────────────────────────────────────────────────── */
function ScoreGlobal({ data }) {
  const sg = data.score_global
  const t = THEME[sg.color] || THEME.green
  const d = sg.scores_por_dimension
  return (
    <div style={{ background: t.bg, border: `3px solid ${t.border}`, borderRadius: 24, padding: '24px 20px', marginBottom: 16, textAlign: 'center', boxShadow: T.sombra }}>
      <p style={{ margin: '0 0 2px', fontSize: 12, color: t.text, textTransform: 'uppercase', fontWeight: 800, letterSpacing: 1 }}>Tu resultado</p>
      <p style={{ fontSize: 60, fontWeight: 800, color: t.text, margin: '4px 0 0', lineHeight: 1, fontFamily: "'Baloo 2', sans-serif" }}>{sg.score_global}</p>
      <p style={{ fontSize: 12, color: t.text, margin: '2px 0 6px', opacity: 0.8 }}>puntos de 100</p>
      <Estrellas n={sg.estrellas} color={t.border} />
      <p style={{ fontSize: 20, fontWeight: 800, color: t.text, margin: '6px 0 4px', fontFamily: "'Baloo 2', sans-serif" }}>{sg.nivel}</p>
      <p style={{ fontSize: 15, color: t.text, margin: 0 }}>{sg.mensaje}</p>
      <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
        {[['Fluidez', d.d1, T.d1], ['Vocabulario', d.d2, T.d2], ['Expresividad', d.d3, T.d3]].map(([lbl, val, col]) => (
          <div key={lbl} style={{ background: '#fff', borderRadius: 14, padding: '12px 6px', boxShadow: '0 2px 6px rgba(0,0,0,0.06)' }}>
            <p style={{ fontSize: 10, color: T.suave, margin: '0 0 4px', fontWeight: 700 }}>{lbl}</p>
            <p style={{ fontSize: 24, fontWeight: 800, color: col, margin: '0 0 4px', fontFamily: "'Baloo 2', sans-serif" }}>{val}</p>
            <div style={{ height: 5, borderRadius: 3, backgroundColor: '#f0e9da' }}>
              <div style={{ height: '100%', width: `${val}%`, borderRadius: 3, backgroundColor: col }} />
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
    <div style={{ marginTop: 12 }}>
      <button onClick={() => setOpen(v => !v)}
        style={{ width: '100%', padding: '9px 14px', borderRadius: 12, border: `2px solid ${T.borde}`, background: '#fbf7ee', color: T.suave, cursor: 'pointer', fontSize: 12, fontWeight: 700, textAlign: 'left' }}>
        {open ? '▲' : '▼'} Datos tecnicos (para el docente)
      </button>
      {open && (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, color: T.texto, marginTop: 6 }}>
          <tbody>
            {rows.map(([k, v]) => (
              <tr key={k} style={{ borderBottom: `1px solid ${T.borde}` }}>
                <td style={{ padding: '5px 8px', color: T.suave }}>{k}</td>
                <td style={{ padding: '5px 8px', fontWeight: 600, textAlign: 'right', color: accentColor || T.texto }}>{v}</td>
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
    <Tarjeta titulo="🗣️ Fluidez al hablar" accentColor={T.d1}>
      <div style={{ background: t.bg, border: `2px solid ${t.border}`, borderRadius: 14, padding: 14, marginBottom: 14, textAlign: 'center' }}>
        <p style={{ fontSize: 17, fontWeight: 800, color: t.text, margin: 0 }}>{fb.mensaje_principal}</p>
        <Estrellas n={fb.estrellas} color={t.border} />
        <button onClick={() => hablar(ttsTexto)}
          style={{ marginTop: 2, padding: '7px 16px', borderRadius: 999, border: `2px solid ${t.border}`, background: '#fff', color: t.text, cursor: 'pointer', fontSize: 13, fontWeight: 700 }}>
          🔊 Escuchar resultado
        </button>
      </div>

      <p style={{ margin: '0 0 4px', fontSize: 13, fontWeight: 800, color: T.texto }}>Velocidad de habla</p>
      <BarraVelocidad ppm={data.ppm.ppm} />
      <Fila label="Palabras por minuto" valor={`${data.ppm.ppm} PPM`} color={data.ppm.ppm >= 80 && data.ppm.ppm <= 120 ? T.verde : T.amarillo} />
      <p style={{ margin: '8px 0 14px', color: T.suave, fontSize: 14 }}>{fb.detalle_velocidad}</p>

      <p style={{ margin: '0 0 6px', fontSize: 13, fontWeight: 800, color: T.texto }}>Bloqueos</p>
      <div style={{ display: 'flex', gap: 20, margin: '4px 0 10px' }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: 40, fontWeight: 800, margin: 0, color: data.pausas.long_pauses === 0 ? T.verde : T.coral, fontFamily: "'Baloo 2', sans-serif" }}>{data.pausas.long_pauses}</p>
          <p style={{ fontSize: 11, color: T.suave, margin: 0 }}>bloqueos</p>
        </div>
      </div>
      <p style={{ margin: '0 0 14px', color: T.suave, fontSize: 14 }}>{fb.detalle_pausas}</p>

      <p style={{ margin: '0 0 4px', fontSize: 13, fontWeight: 800, color: T.texto }}>Volumen</p>
      <Fila label="Volumen de voz" valor={data.prosodia?.intensity_mean_db != null ? `${data.prosodia.intensity_mean_db} dB` : 'N/A'} />
      {data.d3?.detalle_volumen && <p style={{ margin: '8px 0 0', color: T.suave, fontSize: 14 }}>{data.d3.detalle_volumen}</p>}

      <DatosTecnicos rows={tecnico} accentColor={T.d1} />
    </Tarjeta>
  )
}

/* ── D2 ───────────────────────────────────────────────────────────────────── */
function SeccionD2({ d2 }) {
  const colMul = d2.muletillas_count === 0 ? T.verde : d2.muletillas_count <= 3 ? T.amarillo : T.coral
  const colTTR = d2.ttr_score > 0.5 ? T.verde : d2.ttr_score > 0.3 ? T.amarillo : T.coral
  const colCoh = d2.coherencia_nivel === 'bueno' ? T.verde : d2.coherencia_nivel === 'regular' ? T.amarillo : T.coral
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
    <Tarjeta titulo="📚 Vocabulario y coherencia" accentColor={T.d2}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        {[
          ['Muletillas', d2.muletillas_count, '', colMul],
          ['Variedad',   `${Math.round(d2.ttr_score * 100)}%`, 'TTR', colTTR],
          ['Coherencia', d2.coherencia_nivel || '—', '', colCoh],
        ].map(([lbl, val, sub, col]) => (
          <div key={lbl} style={{ flex: 1, textAlign: 'center', background: '#f6f1ff', borderRadius: 12, padding: '12px 4px' }}>
            <p style={{ fontSize: 26, fontWeight: 800, margin: 0, color: col, fontFamily: "'Baloo 2', sans-serif" }}>{val}</p>
            {sub && <p style={{ fontSize: 9, color: T.suave, margin: 0 }}>{sub}</p>}
            <p style={{ fontSize: 11, color: T.suave, margin: '2px 0 0' }}>{lbl}</p>
          </div>
        ))}
      </div>
      <ScoreBar score={d2.score_d2} color={T.d2} />
      <p style={{ margin: '4px 0', color: T.suave, fontSize: 13 }}>{d2.detalle_muletillas}</p>
      <p style={{ margin: '4px 0', color: T.suave, fontSize: 13 }}>{d2.detalle_vocabulario}</p>
      <p style={{ margin: '4px 0', color: T.suave, fontSize: 13 }}>{d2.detalle_coherencia}</p>
      {d2.muletillas_list?.length > 0 && (
        <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 5 }}>
          {d2.muletillas_list.map(m => (
            <span key={m} style={{ padding: '3px 12px', borderRadius: 999, background: '#fff0e6', border: `1.5px solid ${T.naranja}`, color: T.naranja, fontSize: 12, fontWeight: 700 }}>{m}</span>
          ))}
        </div>
      )}
      <DatosTecnicos rows={tecnico} accentColor={T.d2} />
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
    <Tarjeta titulo="🎵 Expresividad de la voz" accentColor={T.d3}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        {[
          ['Variacion tono', d3.breakdown.variacion_tonal_pts, 40, T.naranja],
          ['Calidad voz',    d3.breakdown.calidad_hnr_pts,     30, T.amarillo],
        ].map(([lbl, val, max, col]) => (
          <div key={lbl} style={{ flex: 1, textAlign: 'center', background: '#fff3e6', borderRadius: 12, padding: '12px 4px' }}>
            <p style={{ fontSize: 24, fontWeight: 800, margin: 0, color: col, fontFamily: "'Baloo 2', sans-serif" }}>{val}</p>
            <p style={{ fontSize: 9, color: T.suave, margin: 0 }}>/{max} pts</p>
            <p style={{ fontSize: 11, color: T.suave, margin: '2px 0 0' }}>{lbl}</p>
          </div>
        ))}
      </div>
      <ScoreBar score={d3.score_d3} color={T.d3} />
      <p style={{ margin: '4px 0', color: T.suave, fontSize: 13 }}>{d3.detalle_tono}</p>
      <p style={{ margin: '4px 0', color: T.suave, fontSize: 13 }}>{d3.detalle_calidad}</p>
      <DatosTecnicos rows={tecnico} accentColor={T.d3} />
    </Tarjeta>
  )
}

/* ── Resultados completos ─────────────────────────────────────────────────── */
function Resultados({ data }) {
  const todosConsejos = [...(data.retroalimentacion?.consejos || []), ...(data.d2?.consejos || [])]
  const colorLec = data.lectura
    ? (data.lectura.fidelidad_score >= 70 ? T.verde : data.lectura.fidelidad_score >= 50 ? T.amarillo : T.coral)
    : T.verde
  return (
    <div style={{ maxWidth: 680, margin: '18px auto', textAlign: 'center' }}>
      <ScoreGlobal data={data} />
      {data.lectura && (
        <Tarjeta titulo="📖 Lectura — Fidelidad" accentColor={colorLec}>
          <div style={{ textAlign: 'center', margin: '4px 0 8px' }}>
            <p style={{ fontSize: 46, fontWeight: 800, margin: 0, lineHeight: 1, color: colorLec, fontFamily: "'Baloo 2', sans-serif" }}>{data.lectura.fidelidad_score}%</p>
            <p style={{ fontSize: 11, color: T.suave, margin: '2px 0 0' }}>coincidencia con el texto</p>
          </div>
          <p style={{ margin: '4px 0 8px', color: T.suave, fontSize: 14 }}>{data.lectura.mensaje}</p>
          <Fila label="Palabras del texto" valor={data.lectura.palabras_texto} />
          <Fila label="Palabras leidas"  valor={data.lectura.palabras_leidas} />
        </Tarjeta>
      )}
      <SeccionD1 data={data} />
      <SeccionD2 d2={data.d2} />
      <SeccionD3 d3={data.d3} prosodia={data.prosodia} />
      {todosConsejos.length > 0 && (
        <div style={{ background: '#eaf5ff', border: `2px solid ${T.cielo}`, borderRadius: 18, padding: '16px 20px', marginBottom: 12, textAlign: 'left' }}>
          <p style={{ margin: '0 0 6px', fontWeight: 800, color: T.cielo, fontSize: 14, fontFamily: "'Baloo 2', sans-serif" }}>💡 Para mejorar:</p>
          {todosConsejos.map((c, i) => <p key={i} style={{ margin: '4px 0', color: T.texto, fontSize: 14 }}>• {c}</p>)}
        </div>
      )}
      <Tarjeta titulo="💬 Lo que dijiste">
        <p style={{ margin: 0, color: T.texto, fontSize: 14, lineHeight: 1.7, fontStyle: 'italic' }}>"{data.transcripcion || '(no se detecto texto)'}"</p>
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
      const ws = WaveSurfer.create({ container: containerRef.current, waveColor: T.cielo, progressColor: T.verde, height: 80 })
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

  const descargarPDF = async (id) => {
    try {
      const res = await api.get(`/metrics/reporte/${id}`, { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url; a.download = `reporte_sesion_${id}.pdf`
      document.body.appendChild(a); a.click(); a.remove()
      URL.revokeObjectURL(url)
    } catch { setError('No se pudo descargar el PDF.') }
  }

  const btnColor = analizando ? T.suave : grabando ? T.coral : T.verde

  return (
    <div style={{ minHeight: '100svh', padding: '24px 18px 40px', textAlign: 'center' }}>
      <div style={{ maxWidth: 680, margin: '0 auto' }}>
        <button onClick={() => navigate('/modos')}
          style={{ background: '#fff', border: `2px solid ${T.borde}`, color: T.suave, cursor: 'pointer', fontSize: 13, fontWeight: 700, marginBottom: 16, padding: '8px 16px', borderRadius: 999 }}>
          ← Cambiar modo
        </button>

        <h1 style={{ fontSize: 'clamp(22px,5.5vw,28px)', margin: '0 0 4px' }}>
          {modo === 'lectura' ? '📖 Lee en voz alta' : '🎤 Habla libremente'}
        </h1>
        <p style={{ color: T.suave, margin: '0 0 18px', fontWeight: 700 }}>
          {modo === 'lectura' ? 'Lee el cuento con tu mejor voz' : 'Cuéntanos sobre el tema que quieras'}
        </p>

        {texto && (
          <div style={{ background: '#fff', border: `2px solid ${T.cielo}40`, borderRadius: 20, padding: 20, marginBottom: 18, textAlign: 'left', boxShadow: T.sombra }}>
            <p style={{ color: T.cielo, fontSize: 12, margin: '0 0 8px', textTransform: 'uppercase', fontWeight: 800 }}>{texto.titulo}</p>
            <p style={{ color: T.texto, fontSize: 'clamp(17px,4.5vw,20px)', lineHeight: 1.8, margin: 0 }}>{texto.contenido}</p>
          </div>
        )}

        {modo === 'libre' && !resultado && (
          <div style={{ background: '#eaf5ff', border: `2px solid ${T.cielo}`, borderRadius: 16, padding: '12px 16px', marginBottom: 18 }}>
            <p style={{ color: T.texto, margin: 0, fontSize: 14, fontWeight: 600 }}>💡 Puedes hablar de: tu día, tu animal favorito, tu familia, una película que viste…</p>
          </div>
        )}

        {!resultado && <Lorito size={72} mensaje={grabando ? '¡Te escucho! 👂' : analizando ? 'Pensando…' : '¡Cuando quieras, empieza!'} />}

        <div ref={containerRef} style={{ margin: '0 auto 18px', width: '100%', minHeight: 80, border: `2px solid ${T.borde}`, borderRadius: 18, overflow: 'hidden', background: '#fff' }} />

        <button onClick={manejarGrabacion} disabled={analizando}
          style={{ padding: '16px 44px', fontSize: 18, fontWeight: 800, borderRadius: 999, border: 'none',
            cursor: analizando ? 'not-allowed' : 'pointer', minHeight: 60,
            background: btnColor, color: '#fff', fontFamily: "'Baloo 2', sans-serif",
            boxShadow: `0 5px 0 rgba(0,0,0,0.15)`, opacity: analizando ? 0.7 : 1 }}>
          {analizando ? '⏳ Analizando…' : grabando ? '⏹  Listo, analizar' : '🎤  Empezar a hablar'}
        </button>

        {grabando   && <p style={{ color: T.coral,  marginTop: 12, fontSize: 14, fontWeight: 700 }}>● Grabando… cuando termines presiona el botón</p>}
        {analizando && <p style={{ color: T.suave, marginTop: 14, fontSize: 14 }}>Procesando tu voz con la IA, espera un momentito…</p>}
        {error      && <div style={{ marginTop: 14, background: '#fdecec', border: `2px solid ${T.coral}`, borderRadius: 14, padding: 14, color: T.err, fontSize: 14, fontWeight: 700 }}>{error}</div>}

        {resultado  && <Resultados data={resultado} />}
        {resultado  && (
          <div style={{ marginTop: 14, display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button onClick={() => descargarPDF(resultado.sesion_id)}
              style={{ padding: '12px 26px', borderRadius: 999, border: 'none', background: T.coral, color: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 800, fontFamily: "'Baloo 2', sans-serif", boxShadow: '0 4px 0 rgba(0,0,0,0.15)' }}>
              📄 Descargar PDF
            </button>
            <button onClick={() => navigate('/historial')}
              style={{ padding: '12px 26px', borderRadius: 999, border: `2px solid ${T.borde}`, background: '#fff', color: T.suave, cursor: 'pointer', fontSize: 14, fontWeight: 700 }}>
              📊 Ver mi historial →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
