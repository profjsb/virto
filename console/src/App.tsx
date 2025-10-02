import React, { useEffect, useState } from 'react'
import { api, API_BASE } from './api'
import Login from './Login'
import Sprint from './Sprint'
import RunLogs from './RunLogs'

type Approval = { id:number, description:string, amount_usd:number, status:string, created_at:string }
type Minute = { id:number, name:string, path:string, created_at:string, download?:string }
type UsageSummary = { days:number, total_cost_usd:number, by_model:Record<string, number>, by_actor:Record<string, number>, events:any[] }

export default function App(){
  const [authed, setAuthed] = useState<boolean>(!!localStorage.getItem('token'))
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [minutes, setMinutes] = useState<Minute[]>([])
  const [usage, setUsage] = useState<UsageSummary | null>(null)
  const [desc, setDesc] = useState('Buy domain')
  const [amt, setAmt] = useState(12)
  const [just, setJust] = useState('Launch test')

  const load = async () => {
    const a = await api.get('/ops/approvals')
    setApprovals(a.data)
    const m = await api.get('/ops/minutes')
    setMinutes(m.data)
    const u = await api.get('/ops/usage/summary')
    setUsage(u.data)
  }

  useEffect(() => { if(authed) load() }, [authed])

  if(!authed) return <Login onAuthed={()=>setAuthed(true)} />

  const submitApproval = async () => {
    await api.post('/approvals/submit', { description: desc, amount_usd: amt, justification: just })
    await load()
  }

  const decide = async (id:number, ok:boolean) => {
    await api.patch(`/approvals/${id}/decision`, null, { params: { approved: ok } })
    await load()
  }

  return (
    <div style={{fontFamily:'Inter, system-ui', padding:20, display:'grid', gap:24}}>
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <h1>VO Ops Console</h1><nav style={{display:'flex', gap:12}}><a href='#approvals'>Approvals</a><a href='#sprint'>Sprint</a><a href='#logs'>Run Logs</a><a href='#spend'>Spend</a></nav>
        <button onClick={()=>{localStorage.removeItem('token'); setAuthed(false)}}>Sign out</button>
      </div>

      <section id='approvals' style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:24}}>
        <div>
          <h2>Approvals</h2>
          <div style={{display:'flex', gap:8}}>
            <input placeholder="Description" value={desc} onChange={e=>setDesc(e.target.value)} />
            <input placeholder="Amount" type="number" value={amt} onChange={e=>setAmt(parseFloat(e.target.value))} />
            <input placeholder="Justification" value={just} onChange={e=>setJust(e.target.value)} />
            <button onClick={submitApproval}>Submit</button>
          </div>
          <table style={{width:'100%', marginTop:12}}>
            <thead><tr><th>ID</th><th>Description</th><th>Amount</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              {approvals.map(a=>(
                <tr key={a.id}>
                  <td>{a.id}</td>
                  <td>{a.description}</td>
                  <td>${a.amount_usd}</td>
                  <td>{a.status}</td>
                  <td>
                    <button onClick={()=>decide(a.id, true)}>Approve</button>
                    <button onClick={()=>decide(a.id, false)}>Reject</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div>
          <h2>Minutes</h2>
          <ul>
            {minutes.map(m => <li key={m.id}><code>{m.name}</code> — {m.download ? <a href={m.download.startsWith('http') ? m.download : API_BASE + m.download} target="_blank">download</a> : <small>{m.path}</small>}</li>)}
          </ul>
          <p style={{marginTop:12}}>API base: <code>{API_BASE}</code></p>
        </div>
      </section>

      <section>
        <h2>Spend (last {usage?.days ?? 30} days)</h2>
        {usage && (
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:24}}>
            <div>
              <h3>Total</h3>
              <div style={{fontSize:32}}>${usage.total_cost_usd.toFixed(4)}</div>
              <h4>By Model</h4>
              <ul>{Object.entries(usage.by_model).map(([m,v]) => <li key={m}>{m}: ${v.toFixed(4)}</li>)}</ul>
              <h4>By Actor</h4>
              <ul>{Object.entries(usage.by_actor).map(([m,v]) => <li key={m}>{m}: ${v.toFixed(4)}</li>)}</ul>
            </div>
            <div>
              <h3>Recent Events</h3>
              <table style={{width:'100%'}}>
                <thead><tr><th>ID</th><th>Model</th><th>Actor</th><th>In</th><th>Out</th><th>Cost</th><th>At</th></tr></thead>
                <tbody>
                  {usage.events.map(e => (
                    <tr key={e.id}>
                      <td>{e.id}</td><td>{e.model}</td><td>{e.actor}</td>
                      <td>{e.input_tokens ?? '-'}</td><td>{e.output_tokens ?? '-'}</td>
                      <td>${(e.cost_usd ?? 0).toFixed(4)}</td>
                      <td>{e.created_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}


      <section id='sprint'>
        <Sprint/>
      </section>

      <section id='logs'>
        <RunLogs/>
      </section>

      <section id='spend'>
        <h2>Spend (last {usage?.days ?? 30} days)</h2>
        {usage && (
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:24}}>
            <div>
              <h3>Total</h3>
              <div style={{fontSize:32}}>${usage.total_cost_usd.toFixed(4)}</div>
              <h4>By Model</h4>
              <ul>{Object.entries(usage.by_model).map(([m,v]) => <li key={m}>{m}: ${v.toFixed(4)}</li>)}</ul>
              <h4>By Actor</h4>
              <ul>{Object.entries(usage.by_actor).map(([m,v]) => <li key={m}>{m}: ${v.toFixed(4)}</li>)}</ul>
            </div>
            <div>
              <h3>Recent Events</h3>
              <table style={{width:'100%'}}>
                <thead><tr><th>ID</th><th>Model</th><th>Actor</th><th>In</th><th>Out</th><th>Cost</th><th>At</th></tr></thead>
                <tbody>
                  {usage.events.map(e => (
                    <tr key={e.id}>
                      <td>{e.id}</td><td>{e.model}</td><td>{e.actor}</td>
                      <td>{e.input_tokens ?? '-'}</td><td>{e.output_tokens ?? '-'}</td>
                      <td>${(e.cost_usd ?? 0).toFixed(4)}</td>
                      <td>{e.created_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
