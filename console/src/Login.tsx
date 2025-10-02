import React, { useState } from 'react'
import { api } from './api'

export default function Login({ onAuthed }: { onAuthed: () => void }){
  const [email, setEmail] = useState('admin@example.com')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState<string|undefined>()

  const login = async () => {
    setError(undefined)
    try{
      const r = await api.post('/auth/login', { email, password })
      localStorage.setItem('token', r.data.access_token)
      onAuthed()
    }catch(e:any){
      setError('Login failed')
    }
  }

  return (
    <div style={{display:'grid', placeItems:'center', height:'100vh'}}>
      <div style={{display:'grid', gap:12, padding:24, border:'1px solid #ddd', borderRadius:12, minWidth:320}}>
        <h2>Sign in</h2>
        <input placeholder='Email' value={email} onChange={e=>setEmail(e.target.value)} />
        <input placeholder='Password' type='password' value={password} onChange={e=>setPassword(e.target.value)} />
        <button onClick={login}>Login</button>
        {error && <div style={{color:'red'}}>{error}</div>}
        <small>Tip: if first run, register via API with ALLOW_SIGNUP=true</small>
      </div>
    </div>
  )
}
