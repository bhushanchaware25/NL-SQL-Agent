import { History, X } from 'lucide-react'
import useQueryStore from '../store/queryStore'
import { useWebSocket } from '../hooks/useWebSocket'

export default function Sidebar() {
  const { history, sidebarOpen, toggleSidebar, setQuestion } = useQueryStore()
  const { sendQuery } = useWebSocket()

  const rerun = (question) => {
    setQuestion(question)
    sendQuery(question)
  }

  return (
    <div className={`sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
      <div className="sidebar-header">
        <span className="sidebar-title"><History size={13} style={{ marginRight: 6 }} />History</span>
        <button className="btn btn-ghost" style={{ padding: '4px 8px' }} onClick={toggleSidebar}>
          <X size={14} />
        </button>
      </div>
      <div className="sidebar-list">
        {history.length === 0 && (
          <p className="sidebar-empty">Past queries appear here.</p>
        )}
        {history.map((item, i) => (
          <div key={i} className="sidebar-item" onClick={() => rerun(item.question)} title="Click to re-run">
            <div className="sidebar-item-q">{item.question}</div>
            <div className="sidebar-item-t">{new Date(item.timestamp).toLocaleTimeString()}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
