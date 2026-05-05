import React, { useEffect, useRef, useState } from 'react'
import WaveSurfer from 'wavesurfer.js'
import RecordPlugin from 'wavesurfer.js/dist/plugins/record.js'

function App() {
  const containerRef = useRef(null)
  const wavesurferRef = useRef(null) // Usamos ref para que no se duplique el cuadro
  const [grabando, setGrabando] = useState(false)

  const iniciarGraba = async () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.destroy() // Limpiamos el anterior para que no se agrande el cuadrado
    }

    // Inicializamos Wavesurfer
    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: '#4f46e5',
      progressColor: '#818cf8',
      height: 100,
    })

    const record = ws.registerPlugin(RecordPlugin.create())
    
    try {
      await record.startRecording() // Esto activa el permiso del navegador
      wavesurferRef.current = ws
      setGrabando(true)
    } catch (err) {
      alert("Asegúrate de dar permiso al micrófono en la parte superior del navegador")
    }
  }

  return (
    <div style={{ padding: '50px', textAlign: 'center', backgroundColor: '#1a1a1a', color: 'white', minHeight: '100vh' }}>
      <h1>SRV - Sistema de Oratoria</h1>
      <div 
        ref={containerRef} 
        style={{ margin: '20px auto', width: '80%', minHeight: '100px', border: '1px solid #444', borderRadius: '8px' }}
      ></div>
      <button 
        onClick={iniciarGraba} 
        style={{ padding: '15px 30px', fontSize: '18px', cursor: 'pointer', borderRadius: '8px' }}
      >
        {grabando ? '🎤 Grabando... Habla ahora' : '🚀 Iniciar Práctica'}
      </button>
    </div>
  )
}

export default App