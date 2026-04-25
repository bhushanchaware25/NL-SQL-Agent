import { useState } from 'react'
import { Database, CheckCircle, XCircle, Loader } from 'lucide-react'
import useQueryStore from '../store/queryStore'

export default function DBConnector() {
  const { dbUrl, setDbUrl, setConnected, isConnected, connectedTableCount } = useQueryStore()
  const [inputUrl, setInputUrl] = useState(dbUrl)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleConnect = async () => {
    if (!inputUrl.trim()) {
      // Use default demo DB
      setDbUrl('')
      setConnected(true, 0)
      setError('')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/db/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ database_url: inputUrl.trim() }),
      })
      const data = await res.json()
      if (data.connected) {
        setDbUrl(inputUrl.trim())
        setConnected(true, data.table_count || 0)
      } else {
        setError(data.message || 'Connection failed.')
        setConnected(false)
      }
    } catch {
      setError('Could not reach backend. Is it running?')
      setConnected(false)
    } finally {
      setLoading(false)
    }
  }

  const handleDemo = () => {
    setInputUrl('')
    setDbUrl('')
    setConnected(true, 6)
    setError('')
  }

  return (
    <div className="glass-card db-connector">
      <div className="db-label">
        <Database size={12} style={{ marginRight: 6, verticalAlign: 'middle' }} />
        Database Connection
      </div>
      <div className="db-connector-row">
        <div className="db-input-wrap">
          <input
            className="db-input"
            type="text"
            value={inputUrl}
            onChange={(e) => setInputUrl(e.target.value)}
            placeholder="postgresql://user:password@host:5432/dbname  (leave blank for demo DB)"
            onKeyDown={(e) => e.key === 'Enter' && handleConnect()}
          />
        </div>
        <button className="btn btn-primary" onClick={handleConnect} disabled={loading} style={{ minWidth: 110 }}>
          {loading ? <Loader size={14} className="spin-icon" /> : <CheckCircle size={14} />}
          {loading ? 'Testing…' : 'Connect'}
        </button>
        <button className="btn btn-ghost" onClick={handleDemo} style={{ minWidth: 90 }}>
          Demo DB
        </button>
      </div>
      {error && (
        <p style={{ marginTop: 8, fontSize: '0.78rem', color: 'var(--error)', display: 'flex', gap: 6, alignItems: 'center' }}>
          <XCircle size={13} /> {error}
        </p>
      )}
      {isConnected && !error && (
        <p style={{ marginTop: 8, fontSize: '0.78rem', color: 'var(--success)', display: 'flex', gap: 6, alignItems: 'center' }}>
          <CheckCircle size={13} />
          {dbUrl ? `Connected to custom database${connectedTableCount ? ` (${connectedTableCount} tables)` : ''}` : 'Using demo e-commerce database (6 tables)'}
        </p>
      )}
    </div>
  )
}
