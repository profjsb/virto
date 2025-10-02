import axios from 'axios'
const base = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const api = axios.create({ baseURL: base })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  return config
})

export const API_BASE = base
