import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [schema, setSchema] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const upload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    const res = await axios.post('/upload', formData);
    setPreview(res.data.preview);
    setSchema(res.data.schema);
  };

  const sendMessage = async () => {
    const msg = { sender: 'user', text: input };
    setMessages([...messages, msg]);
    setInput('');
    const res = await axios.post('/chat', { message: input });
    setMessages(m => [...m, msg, { sender: 'bot', data: res.data }]);
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>Data Chat</h1>
      <input type="file" onChange={e => setFile(e.target.files[0])} />
      <button onClick={upload}>Upload</button>
      {preview && (
        <div>
          <h3>Preview</h3>
          <pre>{JSON.stringify(preview, null, 2)}</pre>
        </div>
      )}
      <div style={{ marginTop: 20 }}>
        <input value={input} onChange={e => setInput(e.target.value)} />
        <button onClick={sendMessage}>Send</button>
      </div>
      <div>
        {messages.map((m, i) => (
          <div key={i} style={{ margin: '10px 0' }}>
            <b>{m.sender}:</b>{' '}
            {m.text && <span>{m.text}</span>}
            {m.data && (
              <span>
                {m.data.table && (
                  <table border="1">
                    <tbody>
                      {m.data.table.map((row, ri) => (
                        <tr key={ri}>
                          {Object.values(row).map((cell, ci) => (
                            <td key={ci}>{cell}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                {m.data.image && <img src={m.data.image} alt="chart" />}
                {m.data.error && <pre>{m.data.error}</pre>}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
