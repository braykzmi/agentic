import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export async function uploadFile(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await axios.post(`${API_BASE}/api/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function sendChat(datasetId, question) {
  const { data } = await axios.post(`${API_BASE}/api/chat`, {
    dataset_id: datasetId,
    question,
  })
  return data
}