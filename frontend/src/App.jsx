import { History } from 'lucide-react'
import useQueryStore from './store/queryStore'
import Sidebar from './components/Sidebar'
import DBConnector from './components/DBConnector'
import QueryInput from './components/QueryInput'
import AgentTrace from './components/AgentTrace'
import ResultsPanel from './components/ResultsPanel'

export default function App() {
  const { isConnected, sidebarOpen, toggleSidebar } = useQueryStore()

  return (
    <div className="app-layout">
      <Sidebar />

      <div className="main-area">
        {/* Header */}
        <header className="app-header">
          <div className="app-logo">
            <div className="logo-icon">🤖</div>
            <span>NL<span className="gradient-text">2</span>SQL Agent</span>
          </div>
          <div className="header-actions">
            <span className={`badge ${isConnected ? 'badge-success' : 'badge-warning'}`}>
              {isConnected ? '● Connected' : '○ Not Connected'}
            </span>
            <button className="btn btn-ghost" style={{ padding: '6px 10px' }} onClick={toggleSidebar} title="Toggle history">
              <History size={16} />
            </button>
          </div>
        </header>

        {/* Main content */}
        <div className="content-area">
          <DBConnector />
          <QueryInput />
          <AgentTrace />
          <ResultsPanel />
        </div>
      </div>
    </div>
  )
}
