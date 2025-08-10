import React, { useState } from 'react'
import { sendChat } from '../api'

function Table({ columns, rows }) {
  if (!rows?.length) return null
  const cols = columns?.length ? columns : Object.keys(rows[0])
  return (
    <table className="table">
      <thead><tr>{cols.map(c => <th key={c}>{c}</th>)}</tr></thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>{cols.map(c => <td key={c}>{String(r[c])}</td>)}</tr>
        ))}
      </tbody>
    </table>
  )
}

export default function Chat({ datasetId, preview, schema }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSend() {
    const q = input.trim()
    if (!q || !datasetId) return
    setMessages(m => [...m, { role: 'user', text: q }])
    setInput('')
    setBusy(true)
    try {
      const res = await sendChat(datasetId, q)
      setMessages(m => [...m, {
        role: 'bot',
        text: res.error ? `Error: ${res.error}` : (res.stdout || '').trim() || 'Done.',
        table: res.table,
        columns: res.columns,
        charts: res.charts,
        code: res.generated_code,
        stderr: res.stderr,
      }])
    } catch (err) {
      setMessages(m => [...m, { role: 'bot', text: err?.response?.data?.error || String(err) }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card vstack">
      <div className="small">Dataset ready. Ask a question like <em>“What is the average of column X by column Y?”</em> or <em>“Plot column A over time.”</em></div>
      <div className="hstack">
        <input className="input" value={input} onChange={e => setInput(e.target.value)} placeholder="Ask about your data…" disabled={busy || !datasetId} onKeyDown={e => e.key === 'Enter' && onSend()} />
        <button className="button primary" onClick={onSend} disabled={busy || !datasetId}>Send</button>
      </div>
      <div className="chat">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.text && <div style={{whiteSpace: 'pre-wrap'}}>{m.text}</div>}
            {m.code && <pre className="code"><code>{m.code}</code></pre>}
            {m.table && <Table columns={m.columns} rows={m.table} />}
            {m.stderr && m.stderr.trim() && (
              <details><summary>stderr</summary><pre className="code">{m.stderr}</pre></details>
            )}
            {!!(m.charts?.length) && (
              <div className="images">
                {m.charts.map((u, idx) => <img className="chart" key={idx} src={u} alt={`chart-${idx}`} />)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}