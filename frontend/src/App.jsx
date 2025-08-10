import React, { useState } from 'react'
import './styles.css'
import FileUploader from './components/FileUploader'
import Chat from './components/Chat'

function Preview({ preview, schema }) {
  if (!preview) return null
  return (
    <div className="card vstack">
      <div className="hstack" style={{justifyContent:'space-between'}}>
        <strong>Preview (first 5 rows)</strong>
        <span className="badge">{schema?.nrows} rows • {schema?.ncols} cols</span>
      </div>
      <table className="table">
        <thead>
          <tr>
            {Object.keys(preview[0] || {}).map(k => <th key={k}>{k}</th>)}
          </tr>
        </thead>
        <tbody>
          {preview.map((row, i) => (
            <tr key={i}>{Object.keys(row).map(k => <td key={k}>{String(row[k])}</td>)}</tr>
          ))}
        </tbody>
      </table>
      <div className="vstack">
        <strong>Detected column types</strong>
        <div className="hstack" style={{flexWrap:'wrap', gap: '10px'}}>
          {(schema?.columns || []).map(c => (
            <div key={c.name} className="badge">{c.name}: {c.inferred_type}</div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [dataset, setDataset] = useState(null)

  return (
    <div className="container vstack">
      <h1>No‑Code Data Analysis</h1>
      <p className="small">Upload a CSV/XLSX (≤10 MB), preview schema, then chat to analyze using pandas/matplotlib executed in a Python sandbox.</p>
      <FileUploader onUploaded={setDataset} />
      {dataset?.notes?.length ? (
        <div className="card small">{dataset.notes.join(' ')}</div>
      ) : null}
      {dataset?.preview && <Preview preview={dataset.preview} schema={dataset.schema} />}
      <Chat datasetId={dataset?.dataset_id} preview={dataset?.preview} schema={dataset?.schema} />
    </div>
  )
}