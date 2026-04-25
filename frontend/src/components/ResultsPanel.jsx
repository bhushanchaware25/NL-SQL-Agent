import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import useQueryStore from '../store/queryStore'
import ChartRenderer from './ChartRenderer'

const TABS = [
  { id: 'answer', label: '💬 Answer' },
  { id: 'chart',  label: '📊 Chart' },
  { id: 'table',  label: '📋 Table' },
  { id: 'sql',    label: '🔍 SQL' },
]

export default function ResultsPanel() {
  const { result, activeTab, setActiveTab, isLoading } = useQueryStore()
  const [copied, setCopied] = useState(false)

  const copySQL = () => {
    if (result?.sql) {
      navigator.clipboard.writeText(result.sql)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const visibleTabs = result?.chartType
    ? TABS
    : TABS.filter(t => t.id !== 'chart')

  if (isLoading && !result) {
    return (
      <div className="glass-card results-panel" style={{ alignItems: 'center', justifyContent: 'center' }}>
        <div className="empty-state">
          <div className="spinner" />
          <div className="empty-title">Running your query…</div>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="glass-card results-panel">
        <div className="empty-state" style={{ height: '100%' }}>
          <div className="empty-icon">🤖</div>
          <div className="empty-title">Ask a question</div>
          <div className="empty-sub">Type a natural language question about your database and the AI agent pipeline will generate, execute, and explain the SQL for you.</div>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card results-panel">
      <div className="results-tabs">
        {visibleTabs.map((t) => (
          <button
            key={t.id}
            className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
            {t.id === 'table' && result.rowCount > 0 && (
              <span style={{ marginLeft: 6, fontSize: '0.7rem', color: 'var(--text-muted)' }}>({result.rowCount})</span>
            )}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {activeTab === 'answer' && (
          <div>
            <p className="answer-text">{result.answer}</p>
            <div className="answer-meta">
              <span className="meta-badge">🔄 {result.retryCount} retr{result.retryCount === 1 ? 'y' : 'ies'}</span>
              <span className="meta-badge">📦 {result.rowCount} rows</span>
              {result.chartType && <span className="meta-badge">📊 {result.chartType} chart</span>}
            </div>
          </div>
        )}

        {activeTab === 'chart' && (
          <ChartRenderer chartType={result.chartType} chartData={result.chartData} />
        )}

        {activeTab === 'table' && (
          result.rows?.length > 0 ? (
            <div className="data-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>{Object.keys(result.rows[0]).map((col) => <th key={col}>{col}</th>)}</tr>
                </thead>
                <tbody>
                  {result.rows.map((row, i) => (
                    <tr key={i}>
                      {Object.values(row).map((val, j) => (
                        <td key={j}>
                          {val === null || val === undefined
                            ? <span className="null-val">null</span>
                            : String(val)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state" style={{ height: 200 }}>
              <div className="empty-sub">Query returned 0 rows.</div>
            </div>
          )
        )}

        {activeTab === 'sql' && (
          <div className="sql-block">
            <div className="sql-header">
              <span className="sql-lang-badge">PostgreSQL</span>
              <button className="btn btn-ghost sql-copy-btn" onClick={copySQL}>
                {copied ? <><Check size={12} /> Copied</> : <><Copy size={12} /> Copy</>}
              </button>
            </div>
            <pre className="sql-code">{result.sql}</pre>
            {result.sqlExplanation && (
              <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)', fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                💡 {result.sqlExplanation}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
