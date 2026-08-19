import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE_URL })

// Powers both the log_complaint and edit_complaint tools -- the backend's
// LangGraph intent classifier decides which one runs based on current
// form state, so the frontend doesn't need to know or care which tool fired.
export async function sendChatMessage(sessionId, message) {
  const form = new FormData()
  form.append('session_id', sessionId)
  form.append('message', message)
  const { data } = await api.post('/api/chat', form)
  return data
}

// Powers the extract_document tool.
export async function uploadComplaintDocument(sessionId, file) {
  const form = new FormData()
  form.append('session_id', sessionId)
  form.append('file', file)
  const { data } = await api.post('/api/upload', form)
  return data
}

export async function commitComplaint(sessionId) {
  const { data } = await api.post(`/api/commit/${sessionId}`)
  return data
}

export async function fetchForm(sessionId) {
  const { data } = await api.get(`/api/form/${sessionId}`)
  return data
}
