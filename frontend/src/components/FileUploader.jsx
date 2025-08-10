import React, { useRef, useState } from 'react'
import { uploadFile } from '../api'

export default function FileUploader({ onUploaded }) {
  const inputRef = useRef(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function handleChange(e) {
    setError('')
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 10 * 1024 * 1024) {
      setError('File must be ≤ 10 MB')
      return
    }
    const ok = /\.(csv|xlsx)$/i.test(file.name)
    if (!ok) {
      setError('Please upload a .csv or .xlsx file')
      return
    }
    setBusy(true)
    try {
      const data = await uploadFile(file)
      onUploaded?.(data)
    } catch (err) {
      setError(err?.response?.data?.error || String(err))
    } finally {
      setBusy(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <div className="card vstack">
      <div className="hstack">
        <input ref={inputRef} className="input" type="file" accept=".csv,.xlsx" onChange={handleChange} disabled={busy} />
        <button className="button primary" onClick={() => inputRef.current?.click()} disabled={busy}>Upload</button>
      </div>
      {error && <div style={{color: 'crimson'}}>{error}</div>}
    </div>
  )
}