import useQueryStore from '../store/queryStore'

const STATUS_ICON = {
  running: '⟳',
  done: '✓',
  error: '✕',
  retry: '↺',
}

export default function AgentTrace() {
  const { agentSteps, isLoading } = useQueryStore()

  return (
    <div className="glass-card agent-trace">
      <div className="agent-trace-title">Agent Pipeline</div>

      {agentSteps.length === 0 && !isLoading && (
        <p className="trace-empty">Agent steps will appear here as your query runs…</p>
      )}

      {agentSteps.length === 0 && isLoading && (
        <p className="trace-empty" style={{ color: 'var(--accent)' }}>Initializing pipeline…</p>
      )}

      <div className="agent-steps">
        {agentSteps.map((step, i) => (
          <div key={i} className="agent-step">
            <div className={`step-icon ${step.status}`}>
              {STATUS_ICON[step.status] || '·'}
            </div>
            <div className="step-body">
              <div className="step-agent">{step.agent}</div>
              <div className="step-msg">{step.message}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
