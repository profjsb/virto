import React, { useEffect, useState } from 'react'
import { api } from './api'

type Team = { id:string, key:string, name:string }
type Cycle = { id:string, name:string, number:number, startsAt:string, endsAt:string }
type Issue = { id:string, identifier:string, title:string, url:string, state:{ name:string }, assignee?:{ name:string } }

export default function Sprint(){
  const [teams, setTeams] = useState<Team[]>([])
  const [teamId, setTeamId] = useState<string>('')
  const [cycles, setCycles] = useState<Cycle[]>([])
  const [cycleId, setCycleId] = useState<string>('')
  const [issues, setIssues] = useState<Issue[]>([])
  const [title, setTitle] = useState('Test ticket from console')
  const [desc, setDesc] = useState('Created via API')

  const loadTeams = async () => {
    const r = await api.get('/linear/teams')
    setTeams(r.data); if(r.data.length) setTeamId(r.data[0].id)
  }
  const loadCycles = async (tid:string) => {
    if(!tid) return
    const r = await api.get('/linear/cycles', { params: { team_id: tid, teamId: tid } })
    setCycles(r.data); if(r.data.length) setCycleId(r.data[0].id)
  }
  const loadIssues = async (tid:string, cid:string) => {
    if(!tid || !cid) return
    const r = await api.get('/linear/issues', { params: { team_id: tid, cycle_id: cid, teamId: tid, cycleId: cid } })
    setIssues(r.data)
  }

  useEffect(()=>{ loadTeams() }, [])
  useEffect(()=>{ if(teamId) loadCycles(teamId) }, [teamId])
  useEffect(()=>{ if(teamId && cycleId) loadIssues(teamId, cycleId) }, [teamId, cycleId])

  const create = async () => {
    await api.post('/linear/issues', { team_id: teamId, title, description: desc })
    await loadIssues(teamId, cycleId)
  }

  return (
    <div style={{display:'grid', gap:12}}>
      <h2>Sprint (Linear)</h2>
      <div style={{display:'flex', gap:8}}>
        <select value={teamId} onChange={e=>setTeamId(e.target.value)}>{teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}</select>
        <select value={cycleId} onChange={e=>setCycleId(e.target.value)}>{cycles.map(c => <option key={c.id} value={c.id}>{c.name || ('Cycle '+c.number)}</option>)}</select>
        <button onClick={()=>loadIssues(teamId, cycleId)}>Refresh</button>
      </div>
      <div style={{display:'flex', gap:8}}>
        <input placeholder="Title" value={title} onChange={e=>setTitle(e.target.value)} />
        <input placeholder="Description" value={desc} onChange={e=>setDesc(e.target.value)} />
        <button onClick={create}>Create Issue</button>
      </div>
      <table style={{width:'100%', marginTop:12}}>
        <thead><tr><th>ID</th><th>Title</th><th>State</th><th>Assignee</th><th>Link</th></tr></thead>
        <tbody>
          {issues.map(i => (
            <tr key={i.id}>
              <td>{i.identifier}</td>
              <td>{i.title}</td>
              <td>{i.state?.name}</td>
              <td>{i.assignee?.name || '-'}</td>
              <td><a href={i.url} target="_blank" rel="noreferrer">open</a></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
