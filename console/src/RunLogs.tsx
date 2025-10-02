import React, { useEffect, useState } from 'react'
import { api, API_BASE } from './api'

export default function RunLogs(){
  const [runId, setRunId] = useState<number|undefined>()
  const [lines, setLines] = useState<string[]>([])

  const start = async () => {
    const r = await api.post('/runs/start_demo')
    const id = r.data.run_id
    setRunId(id)
    const es = new EventSource(`${API_BASE}/streams/runs/${id}`, { withCredentials: false })
    es.addEventListener('log', (e:any) => setLines(prev => [...prev, e.data]))
    es.addEventListener('done', (e:any) => { setLines(prev => [...prev, 'DONE']); es.close() })
    es.onerror = () => { es.close() }
  }

  return (
    <div style={{display:'grid', gap:12}}>
      <h2>Live Run Logs</h2>
      <button onClick={start}>Start Demo Run</button>
      {runId && <div>Run ID: {runId}</div>}
      <pre style={{background:'#111', color:'#0f0', padding:12, minHeight:200, borderRadius:8}}>
        {lines.join('\n')}
      </pre>
    </div>
  )
}
