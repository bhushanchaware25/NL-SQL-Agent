import { useRef } from 'react'
import { Send, Loader2 } from 'lucide-react'
import useQueryStore from '../store/queryStore'
import { useWebSocket } from '../hooks/useWebSocket'

const EXAMPLES = [
  'Top 5 products by revenue',
  'Monthly revenue last 6 months',
  'Customers with no orders',
  'Average order value by city',
  'Products rated below 3 stars',
]

export default function QueryInput() {
  const { question, setQuestion, isLoading } = useQueryStore()
  const { sendQuery } = useWebSocket()
  const textareaRef = useRef(null)

  const handleSend = () => {
    if (!question.trim() || isLoading) return
    sendQuery(question.trim())
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="glass-card query-input-card">
      <div className="query-textarea-wrap">
        <textarea
          ref={textareaRef}
          className="query-textarea"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about your database… e.g. 'What are the top 5 products by revenue last month?'"
          disabled={isLoading}
        />
        <button
          className="btn btn-primary query-send-btn"
          onClick={handleSend}
          disabled={isLoading || !question.trim()}
        >
          {isLoading ? <Loader2 size={15} className="spin-icon" /> : <Send size={15} />}
          {isLoading ? 'Running…' : 'Ask'}
        </button>
      </div>
      <div className="query-hint">
        <span style={{ color: 'var(--text-muted)' }}>Try: </span>
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => { setQuestion(ex); setTimeout(handleSend, 50) }}
            disabled={isLoading}
            style={{
              background: 'none', border: 'none', color: 'var(--accent)',
              cursor: 'pointer', fontSize: '0.75rem', padding: '0 6px 0 0',
              fontFamily: 'inherit', transition: 'color 0.15s',
            }}
            onMouseEnter={(e) => (e.target.style.color = 'var(--accent-hover)')}
            onMouseLeave={(e) => (e.target.style.color = 'var(--accent)')}
          >
            {ex}
          </button>
        ))}
        <span style={{ color: 'var(--text-muted)', marginLeft: 8 }}>· Ctrl+Enter to send</span>
      </div>
    </div>
  )
}
